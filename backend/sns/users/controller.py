from typing import List
import secrets

from fastapi import APIRouter, Depends, status, HTTPException, Body
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.common.config import settings
from sns.users.model import User
from sns.users.schema import (
    UserPasswordUpdate,
    UserCreate,
    UserUpdate,
    UserRead,
    UserBase,
    Token,
    Msg,
)
from sns.users.repositories.db import user_crud, follow_crud
from sns.users.service import (
    get_current_user_verified,
    send_reset_password_email,
    send_new_account_email,
    create_access_token,
    get_password_hash,
    verify_password,
    is_verified,
    get_user,
    create,
    update,
    delete,
)


router = APIRouter()


@router.post("/signup", response_model=Msg, status_code=status.HTTP_201_CREATED)
def signup(
    signup_info: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db),
):
    """email과 password로 새 user를 등록한다.

    Args: \\
        - signup_info (schema.UserCreate) : 등록할 email과 password 정보

    Returns: \\
        - 새로 생성한 User 객체를 반환한다.
    """
    if (
        not signup_info.email
        or not signup_info.password
        or not signup_info.password_confirm
    ):
        raise HTTPException(status_code=400, detail="가입 정보를 다 입력하지 않았습니다.")

    if signup_info.password != signup_info.password_confirm:
        raise HTTPException(status_code=400, detail="비밀번호 정보가 일치하지 않습니다.")

    user = get_user(db, email=signup_info.email)
    if user:
        if is_verified(user):
            raise HTTPException(status_code=403, detail="이미 인증된 이메일입니다.")
        else:
            raise HTTPException(status_code=403, detail="인증 완료되지 못한 이메일입니다.")

    # 비활성화 유저 생성
    new_user = create(db, signup_info)

    # 이메일 인증 메일 발송하기
    try:
        code = secrets.token_urlsafe(10)
        new_user = get_user(db, email=signup_info.email)
        update(db, user=new_user, user_info={"verification_code": code})
        db.commit()
        url = f"http://0.0.0.0:8000{settings.API_V1_STR}/verification-email/{code}"
        data = {
            "email_to": signup_info.email,
            "url": url,
        }
        background_tasks.add_task(send_new_account_email, **data)
    except Exception:
        delete(db, new_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이메일 발송 과정에서 에러가 발생했습니다. 다시 회원가입 정보를 입력하세요",
        )
    return {"status": "success", "msg": "이메일 전송이 완료되었습니다."}


@router.patch(
    "/verification-email/{code}", response_model=Msg, status_code=status.HTTP_200_OK
)
def verify_email(code: str, db: Session = Depends(db.get_db)):
    """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

    Args: \\
        - code (str) : url에 담겨진 code 정보

    Returns: \\
        - Msg: 계정 인증 완료 메세지
    """
    user = db.query(User).filter(User.verification_code == code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록되지 않은 인증 링크입니다."
        )
    update(db, user=user, user_info={"verified": True})
    return {"status": "success", "msg": "이메일 인증이 완료되었습니다."}


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(
    email: str = Body(...), password: str = Body(...), db: Session = Depends(db.get_db)
):
    """login 정보를 입력하면 access token을 발행한다.

    Args: \\
        - email: 로그인 시 입력한 email    
        - password: 로그인 시 입력한 password  

    Returns: \\
        - dict: 입력한 정보가 정확하면 access token을 발행한다.
    """
    user = get_user(db, email=email, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이메일 또는 비밀번호 정보가 정확하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not is_verified(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="먼저 이메일 인증을 완료하세요.",
        )
    access_token = create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/password-reset", response_model=Msg, status_code=status.HTTP_200_OK)
def reset_password(
    email: str = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(db.get_db),
):
    """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

    Args: \\
        - email: 로그인 시 입력한 이메일 주소  

    Returns: \\
        - Msg: 비밀번호 초기화 이메일 송신 완료 메세지
    """
    user = get_user(db, email=email)
    if user:
        if is_verified(user):
            try:
                temporary_password = secrets.token_urlsafe(8)
                update(db, user, {"password": get_password_hash(temporary_password)})
                data = {"email_to": email, "password": temporary_password}
                background_tasks.add_task(send_reset_password_email, **data)
                return {"status": "success", "msg": "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."}
            except Exception:
                raise
        else:
            raise HTTPException(status_code=403, detail="먼저 이메일 인증을 완료하세요.")
    else:
        raise HTTPException(status_code=403, detail="등록된 회원이 아닙니다.")


@router.patch("/password-change", response_model=Msg, status_code=status.HTTP_200_OK)
def change_password(
    password_info: UserPasswordUpdate,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """임시 비밀번호로 로그인 후, 다른 패스워드로 변경한다.
       기존 패스워드 정보가 현재 유저의 패스워드 정보와 일치하면 새로운 패스워드로 변경한다.
       일치하지 않으면 변경하지 않는다.  

    Args: \\
        password_info (UserPasswordUpdate): 현재 패스워드와 새 패스워드 정보
        current_user (UserBase): 현재 유저 정보

    Returns: \\
        Msg: 실행 완료 메세지
    """
    current_password, new_password = (
        password_info.current_password,
        password_info.new_password,
    )

    user = get_user(db, email=current_user.email)

    if verify_password(current_password, user.password):
        try:
            user = get_user(db, email=current_user.email)
            update(db, user, {"password": get_password_hash(new_password)})
            return {"status": "success", "msg": "비밀번호가 변경되었습니다."}
        except Exception:
            raise HTTPException(status_code=500, detail="비밀번호 변경에 실패했습니다.")
    else:
        raise HTTPException(status_code=400, detail="입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다.")


@router.get(
    "/users/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def read_user(
    user_id: int,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id가 current_user와의 일치 유무에 따라 다른 user 정보를 반환한다.

    Args: \\
        - user_id (int): db에 저장된 user id
        - current_user (UserBase): 현재 유저 정보

    Returns: \\
        - 유저 정보
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.email == current_user.email:
            return get_user(db, email=current_user.email)
        else:
            data = {
                "name": selected_user.name,
                "profile_text": selected_user.profile_text,
            }
            return data
    else:
        raise HTTPException(status_code=400, detail="등록되지 않은 유저입니다.")


@router.patch(
    "/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK
)
def update_user(
    user_id: int,
    info_to_be_updated: UserUpdate,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 정보를 수정한다.

    Args: \\
        - user_id (int): db에 저장된 user id
        - info_to_be_updated (UserUpdate): 업데이트할 user 정보
        - current_user (UserBase): token에서 가져온 현재 유저 정보

    Returns: \\
        - Msg: 실행 완료 메세지
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user.email == current_user.email:
        try:
            user_to_update = get_user(db, email=current_user.email)
            user = update(db, user_to_update, info_to_be_updated)
            return user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 정보 변경에 실패하였습니다.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="수정할 권한이 없습니다."
        )


@router.delete("/users/{user_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 계정을 삭제한다.

    Args: \\
        - user_id (int): db에 저장된 user id
        - current_user (User, optional): token에서 가져온 현재 유저 정보

    Returns: \\
        - Msg: 계정 삭제 완료 메세지
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user.email == current_user.email:
        try:
            user_to_delete = get_user(db, email=current_user.email)
            delete(db, user_to_delete)
            return {"status": "success", "msg": "계정이 삭제되었습니다."}
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 삭제를 실패하였습니다.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="삭제할 권한이 없습니다."
        )


@router.get(
    "/users/{user_id}/followers",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_followers(
    user_id: int,
    db: Session = Depends(db.get_db),
) -> List[UserBase]:
    followers = follow_crud.get_followers(db, following_id=user_id)
    return followers


@router.get(
    "/users/{user_id}/followings",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_followings(
    user_id: int,
    db: Session = Depends(db.get_db),
) -> List[UserBase]:
    followings = follow_crud.get_followings(db, follower_id=user_id)
    return followings


@router.post("/follow/{user_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def follow_user(
    user_id: int,
    current_user: UserBase = Depends(user_crud.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    data = Follow(following_id=current_user.id, follower_id=user_id)
    follow_object = follow_crud.follow(db, follow_info=data)
    if follow_object:
        return {"status": "success", "msg": "follow 관계가 맺어졌습니다."}
    else:
        return {"status": "fail", "msg": "follow 관계가 실패했습니다."}


@router.post("/unfollow/{user_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def unfollower_user(
    user_id: int,
    current_user: UserBase = Depends(user_crud.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    data = Unfollow(following_id=current_user.id, follower_id=user_id)
    follow_object = follow_crud.follow(db, follow_info=data)
    if follow_object:
        return {"status": "success", "msg": "follow 관계 취소가 완료되었습니다."}
    else:
        return {"status": "fail", "msg": "follow 관계 취소가 실패했습니다."}
