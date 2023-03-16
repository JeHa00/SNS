from datetime import timedelta
import secrets

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from sns.common.session import db
from sns.common.config import settings
from sns.users.model import User
from sns.users.schema import Token, UserBase, UserCreate, UserUpdate, UserRead
from sns.users.service import (
    create,
    update,
    delete,
    get_user,
    create_access_token,
    send_new_account_email,
    is_verified,
)


router = APIRouter()


@router.post("/signup", response_model=UserBase, status_code=status.HTTP_201_CREATED)
def signup(
    signup_info: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(db.get_db),
):
    """email과 password로 새 user를 등록한다.

    Args: \\
        - **signup_info (schema.UserCreate)** : user로 등록할 email과 password 정보 \\
        - **db (Session, optional)** : db session

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
        if not is_verified(user):
            raise HTTPException(status_code=400, detail="인증 완료되지 못한 이메일입니다.")

        if is_verified(user):
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

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
            "password": signup_info.password,
            "url": url,
        }
        background_tasks.add_task(send_new_account_email, **data)
    except Exception:
        delete(db, new_user)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이메일 발송 과정에서 에러가 발생했습니다.",
        )
    return new_user


@router.post("/verification-email/{code}", status_code=status.HTTP_200_OK)
def verify_email(code: str, db: Session = Depends(db.get_db)) -> JSONResponse:
    """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

    Args: \\
        - **code (str)** : url에 담겨진 code 정보 \\
        - **db (Session, optional)** : db session

    Raises: \\
       - **HTTPException** : code 정보를 가진 user가 없을 경우 403 error를 발생한다.

    Returns: \\
        - **JSONResponse** : 계정 인증 완료
    """
    user = db.query(User).filter(User.verification_code == code).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록되지 않은 인증 링크입니다."
        )
    update(db, user=user, user_info={"verified": True})
    return JSONResponse(status_code=200, content="계정 인증을 성공적으로 완료했습니다.")


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(login_info: UserBase, db: Session = Depends(db.get_db)) -> dict:
    """login 정보를 입력하면 access token을 발행한다.

    Args: \\
        - **login_info (schema.UserBase)**: 로그인 시 입력한 email과 password를 의미한다. \\
        - **db (Session, optional)**: db session.

    Raises: \\
        - HTTPException: 입력한 email 또는 password 정보가 정확하지 않으면 401 error를 발생시킨다.

    Returns: \\
        - **dict**: 입력한 정보가 정확하면 access token을 발행한다.
    """

    user = get_user(db, email=login_info.email, password=login_info.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호 정보가 정확하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_email": user.email}, expires_delta=token_expires
    )
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: Session = Depends(db.get_db)):
    # 토큰 소거
    pass


@router.post(
    "/password-reset", response_model=UserUpdate, status_code=status.HTTP_200_OK
)
def reset_password(db: Session = Depends(db.get_db)):
    # 입력한 이메일로 비밀번호 바꾸기
    pass


@router.get(
    "/users/{user_id}/profile",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def get_user_profile(
    user_id: int,
    db: Session = Depends(db.get_db),
):
    # {user_id}에 해당되는 profile 정보 보내기
    pass


@router.patch(
    "/users/{user_id}", response_model=UserUpdate, status_code=status.HTTP_200_OK
)
def update_user(user_id: int, db: Session = Depends(db.get_db)):
    # 프로필 관련 정보 또는 비밀번호 수정
    pass


@router.post("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(db.get_db)):
    pass
