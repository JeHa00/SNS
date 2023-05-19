from fastapi import APIRouter, Depends, status, Body
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import UserService
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
    user_service=Depends(UserService),
    db: Session = Depends(db.get_db),
):
    """email과 password로 새 user를 등록한다.

    Args:

    - data_for_signup (schema.UserCreate) : 등록할 email과 password 정보

    Raises:

    - HTTPException (403 FORBIDDEN): 다음 2가지 경우에 발생한다.
        - 회원 가입 시 입력한 이메일이 이미 인증되었을 때
        - 이미 등록은 되었고, 인증은 안되었을 때
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생한다.
        - 유저 생성에 실패했을 때
        - 이메일 인증을 위한 이메일 발송에 실패했을 때


    Returns:

    - Msg: 이메일 전송 성공 유무 메세지 반환
    """
    user_service.signup(
        db,
        background_tasks,
        data_for_signup,
    )
    return {"status": "success", "msg": "이메일 전송이 완료되었습니다."}


@router.patch(
    "/verification-email/{code}",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    code: str,
    user_service=Depends(UserService),
    db: Session = Depends(db.get_db),
):
    """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

    Args:

    - code (str) : url에 담겨진 인증 code 정보

    Raises:

    - HTTPException (404 NOT FOUND): 다음 경우에 발생한다.
        - verification code가 code 값과 일치하는 user를 찾지 못할 때 발생한다.
    - HTTPException (500 INTERNAL SERVER ERROR): 인증 상태값 변경에 실패했을 때 발생한다.

    Returns:

    - Msg: 계정 인증 완료 메세지
    """
    user_service.verify_email(
        db,
        code,
    )
    return {"status": "success", "msg": "이메일 인증이 완료되었습니다."}


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(
    email: str = Body(...),
    password: str = Body(...),
    user_service=Depends(UserService),
    db: Session = Depends(db.get_db),
):
    """login 정보를 입력하면 access token을 발행한다.

    Args:

    - email: 로그인 시 입력한 email
    - password: 로그인 시 입력한 password

    Raises:

    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
    - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다를 때 발생
    - HTTPException (403 FORBIDDEN): 등록은 했지만 이메일 인증이 완료되지 못한 계정일 때 발생

    Returns:

    - dict: 입력한 정보가 정확하면 access token을 발행한다.
    """
    access_token = user_service.login(
        db,
        email,
        password,
    )
    return {"access_token": access_token, "token_type": "Bearer"}


@router.post("/password-reset", response_model=Msg, status_code=status.HTTP_200_OK)
def reset_password(
    email: str = Body(...),
    user_service=Depends(UserService),
    background_tasks=BackgroundTasks(),
    db: Session = Depends(db.get_db),
):
    """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

    Args:

    - email: 로그인 시 입력한 이메일 주소

    Raises:

    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
    - HTTPException (403 FORBIDDEN): 등록은 했지만 이메일 인증이 완료되지 못한 계정일 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 경우에 발생한다.
        - 비밀번호 초기화를 위한 이메일 발송에 실패했을 때

    Returns:

    - Msg: 비밀번호 초기화 이메일 송신 완료 메세지
    """
    user_service.reset_password(
        db,
        email,
        background_tasks,
    )
    return {"status": "success", "msg": "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."}


@router.patch("/password-change", response_model=Msg, status_code=status.HTTP_200_OK)
def change_password(
    password_data: UserPasswordUpdate,
    user_service=Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """임시 비밀번호로 로그인 후, 다른 패스워드로 변경한다.
        기존 패스워드 정보가 현재 유저의 패스워드 정보와 일치하면 새로운 패스워드로 변경한다.
        일치하지 않으면 변경하지 않는다.

     Args:

     - password_data (UserPasswordUpdate): 현재 패스워드와 새 패스워드 정보
     - current_user (UserBase): 현재 유저 정보

    Raises:

    - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
    - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다를 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): 비밀번호 변경에 실패했을 때 발생한다.

     Returns:

     - Msg: 실행 완료 메세지
    """
    user_service.change_password(
        db,
        password_data,
        current_user,
    )
    return {"status": "success", "msg": "비밀번호가 변경되었습니다."}


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
)
def read_user(
    user_id: int,
    user_service=Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id가 current_user와의 일치 유무에 따라 user 정보를 반환한다.

    - user_id가 current_user와 동일하면 email을 포함한 current_user의 정보를 전달한다.
    - user_id와 current_user가 다르면 user_id에 해당되는 name과 profile text를 전달한다.

    Args:

    - user_id (int): db에 저장된 user id
    - current_user (UserBase): 현재 유저 정보

    Raises:

    - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생

    Returns:

    - User or dict: 조회된 유저 정보
    """
    user_data = user_service.read_user(
        db,
        user_id,
        current_user,
    )
    return user_data


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    data_to_be_updated: UserUpdate,
    user_service=Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> UserRead:
    """user_id와 현재 user id와 같으면 유저 자신의 정보를 수정한다.

    Args:

    - user_id (int): db에 저장된 user id
    - data_to_be_updated (UserUpdate): 업데이트할 user 정보
    - current_user (UserBase): token에서 가져온 현재 유저 정보

    Raises:

    - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 변경에 실패했을 때 발생
    - HTTPException (401 UNAUTHORIZED): 변경 권한이 없음을 나타내는 에러

    Returns:

    - UserRead: 업데이트된 user 정보를 반환
    """
    updated_user = user_service.update_user(
        db,
        user_id,
        data_to_be_updated,
        current_user,
    )
    return updated_user


@router.delete("/users/{user_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    user_service=Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 계정을 삭제한다.

    Args:

    - user_id (int): db에 저장된 user id
    - current_user (User, optional): token에서 가져온 현재 유저 정보

    Raises:

    - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 삭제에 실패했을 때 발생
    - HTTPException (401 UNAUTHORIZED): 삭제 권한이 없음을 나타내는 에러

    Returns:

    - Msg: 계정 삭제 완료 메세지
    """
    user_service.delete_user(
        db,
        user_id,
        current_user,
    )
    return {"status": "success", "msg": "계정이 삭제되었습니다."}
