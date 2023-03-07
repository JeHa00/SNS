from datetime import timedelta

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.common.config import settings
from sns.users.schema import Token, UserBase, UserCreate, UserUpdate, UserRead
from sns.users.service import create_user, get_user, create_access_token

router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(
    signup_info: UserCreate,
    db: Session = Depends(db.get_db),
):
    """email과 password로 user 등록하기

    Args: \\
        - **signup_info (schema.UserCreate)** : user로 등록할 email과 password 정보 \\
        - **db (Session, optional)** : db session

    Returns: \\
        - 새로 생성한 User 객체를 반환한다.
    """
    # 가입 이메일과 비밀번호를 다 입력했는지
    if (
        not signup_info.email
        or not signup_info.password
        or not signup_info.password_confirm
    ):
        raise HTTPException(status_code=400, detail="가입 정보를 다 입력하지 않았습니다.")

    # 기존에 등록한 이메일이 존재하는지
    if get_user(db, email=signup_info.email):
        raise HTTPException(status_code=400, detail="존재하는 email입니다.")

    # password가 일치한지
    if signup_info.password != signup_info.password_confirm:
        raise HTTPException(status_code=400, detail="비밀번호 정보가 일치하지 않습니다.")

    # 입력된 이메일로 확인 이메일 보내기

    # 해당 응답결과에 따라서 이메일 인증 완료 후, 가입 진행
    # 일정 시간이 지나면 회원 가입 진행 중단

    # 이메일 인증 완료 후, 비밀번호는 해쉬화하기 -> service.py

    new_user = create_user(signup_info)
    return new_user


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
    return {"access_token": access_token, "token_type": "bearer"}


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
