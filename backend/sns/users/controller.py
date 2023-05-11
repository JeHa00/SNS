# controller.py
from fastapi import APIRouter, Depends, status, HTTPException, Body
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import user_service
from sns.users.schema import (
    UserPasswordUpdate,
    UserCreate,
    UserUpdate,
    UserBase,
    UserRead,
    Token,
    Msg,
)


router = APIRouter()


@router.post("/signup", response_model=Msg, status_code=status.HTTP_201_CREATED)
def signup(
    data_for_signup: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db),
):
    """email과 password로 새 user를 등록한다.

    Args:

    - data_for_signup (schema.UserCreate) : 등록할 email과 password 정보

    Returns:

    - Msg: 이메일 전송 성공 유무 메세지 반환
    """
    user = user_service.get_user(db, email=data_for_signup.email)

    if user and user_service.is_verified(user):
        raise HTTPException(status_code=403, detail="이미 인증된 이메일입니다.")

    user_service.create(db, data_for_signup)  # 미인증 유저 생성

    # 이메일 인증 메일 발송하기
    user_service.send_verification_email(
        db, email=data_for_signup.email, background_tasks=background_tasks
    )
    return {"status": "success", "msg": "이메일 전송이 완료되었습니다."}


@router.patch(
    "/verification-email/{code}", response_model=Msg, status_code=status.HTTP_200_OK
)
def verify_email(code: str, db: Session = Depends(db.get_db)):
    """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

    Args:

    - code (str) : url에 담겨진 인증 code 정보

    Returns:

    - Msg: 계정 인증 완료 메세지
    """
    user = user_service.get_user(db, verification_code=code)
    user_service.update(db, user=user, data_to_be_updated={"verified": True})
    return {"status": "success", "msg": "이메일 인증이 완료되었습니다."}


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(
    email: str = Body(...), password: str = Body(...), db: Session = Depends(db.get_db)
):
    """login 정보를 입력하면 access token을 발행한다.

    Args:

    - email: 로그인 시 입력한 email
    - password: 로그인 시 입력한 password

    Returns:

    - dict: 입력한 정보가 정확하면 access token을 발행한다.
    """
    user = user_service.get_user(db, email=email, password=password)

    if user_service.is_verified(user):
        access_token = user_service.create_access_token(data={"sub": email})
        return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/password-reset", response_model=Msg, status_code=status.HTTP_200_OK)
def reset_password(
    email: str = Body(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(db.get_db),
):
    """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

    Args:

    - email: 로그인 시 입력한 이메일 주소

    Returns:

    - Msg: 비밀번호 초기화 이메일 송신 완료 메세지
    """
    user = user_service.get_user(db, email=email)

    if user_service.is_verified(user):
        user_service.send_password_reset_email(db, email, background_tasks)
        return {"status": "success", "msg": "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."}


@router.patch("/password-change", response_model=Msg, status_code=status.HTTP_200_OK)
def change_password(
    password_data: UserPasswordUpdate,
    current_user: UserBase = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """임시 비밀번호로 로그인 후, 다른 패스워드로 변경한다.
       기존 패스워드 정보가 현재 유저의 패스워드 정보와 일치하면 새로운 패스워드로 변경한다.
       일치하지 않으면 변경하지 않는다.

    Args:

    - password_data (UserPasswordUpdate): 현재 패스워드와 새 패스워드 정보
    - current_user (UserBase): 현재 유저 정보

    Returns:

    - Msg: 실행 완료 메세지
    """
    user = user_service.get_user(db, email=current_user.email)

    if user_service.verify_password(password_data.current_password, user.password):
        user_service.update(
            db,
            user,
            {"password": user_service.get_password_hash(password_data.new_password)},
        )
        return {"status": "success", "msg": "비밀번호가 변경되었습니다."}


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
)
def read_user(
    user_id: int,
    current_user: UserBase = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id가 current_user와의 일치 유무에 따라 다른 user 정보를 반환한다.

    Args:

    - user_id (int): db에 저장된 user id
    - current_user (UserBase): 현재 유저 정보

    Returns:

    - User or dict: 유저 정보
    """
    selected_user = user_service.get_user(db, user_id=user_id)
    if selected_user:
        if selected_user.email == current_user.email:
            return selected_user
        else:
            data = {
                "name": selected_user.name,
                "profile_text": selected_user.profile_text,
            }
            return data


@router.patch(
    "/users/{user_id}", response_model=UserRead, status_code=status.HTTP_200_OK
)
def update_user(
    user_id: int,
    data_to_be_updated: UserUpdate,
    current_user: UserBase = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 정보를 수정한다.

    Args:

    - user_id (int): db에 저장된 user id
    - data_to_be_updated (UserUpdate): 업데이트할 user 정보
    - current_user (UserBase): token에서 가져온 현재 유저 정보

    Returns:

    - Msg: 실행 완료 메세지
    """
    selected_user = user_service.get_user(db, user_id=user_id)
    if selected_user.email == current_user.email:
        user_to_be_updated = user_service.get_user(db, email=current_user.email)
        user = user_service.update(db, user_to_be_updated, data_to_be_updated)
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="수정할 권한이 없습니다."
        )


@router.delete("/users/{user_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    current_user: UserBase = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 계정을 삭제한다.

    Args:

    - user_id (int): db에 저장된 user id
    - current_user (User, optional): token에서 가져온 현재 유저 정보

    Returns:

    - Msg: 계정 삭제 완료 메세지
    """
    selected_user = user_service.get_user(db, user_id=user_id)
    if selected_user.email == current_user.email:
        user_to_be_delete = user_service.get_user(db, email=current_user.email)
        user_service.remove(db, user_to_be_delete)
        return {"status": "success", "msg": "계정이 삭제되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="삭제할 권한이 없습니다."
        )
