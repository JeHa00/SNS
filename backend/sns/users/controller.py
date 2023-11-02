from typing import List

from fastapi import APIRouter, Depends, status, Body
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.common.session import db, redis_db
from sns.users.repositories.email_client import EmailClient
from sns.users.service import UserService
from sns.users.schema import (
    UserPasswordUpdate,
    UserCreate,
    UserUpdate,
    UserRead,
    UserBase,
    Token,
    Message,
)


router = APIRouter()


@router.post(
    "/signup",
    response_model=Message,
    status_code=status.HTTP_201_CREATED,
)
def signup(
    data_for_signup: UserCreate,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(UserService),
    email_client: EmailClient = Depends(EmailClient),
    db: Session = Depends(db.get_db),
):
    """email과 password로 새 user를 등록한다.

    Args:

    - data_for_signup (schema.UserCreate) : 등록할 email과 password 정보
        - email: 가입 시 입력할 이메일 주소
        - password: 가입 시 입력할 패스워드
        - password_confirm: 위 패스워드에 대한 확인 패스워드

    Raises:

    - HTTPException (400 BAD REQUEST): 이미 인증된 이메일인 경우
    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생한다.
        - 유저 생성에 실패할 경우 (code: FAILED_TO_CREATE)
        - 이메일 인증을 위한 이메일 발송에 실패할 경우 (code: FAILED_TO_SEND_A_EMAIL)

    Returns:

    - Message: 이메일 전송 성공 유무 메세지 반환
    """
    user_service.signup(
        db,
        email_client,
        background_tasks,
        data_for_signup.dict(),
    )
    return {"status": "success", "message": "이메일 전송이 완료되었습니다."}


@router.post(
    "/verification-email/{code}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def verify_email(
    code: str,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(db.get_db),
):
    """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

    Args:

    - code (str) : url에 담겨진 인증 code 정보

    Raises:

    - HTTPException (404 NOT FOUND): 다음 경우에 발생한다.
        - verification code가 code 값과 일치하는 user를 찾지 못한 경우 (code: USER_NOT_FOUND)
    - HTTPException (500 INTERNAL SERVER ERROR): 인증 상태값 변경에 실패한 경우

    Returns:

    - Message: 계정 인증 완료 메세지
    """
    user_service.verify_email(
        db,
        code,
    )
    return {"status": "success", "message": "이메일 인증이 완료되었습니다."}


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
def login(
    email: str = Body(...),
    password: str = Body(...),
    user_service: UserService = Depends(UserService),
    db: Session = Depends(db.get_db),
):
    """login 정보를 입력하면 access token을 발행한다.

    Args:

    - email: 로그인 시 입력한 email
    - password: 로그인 시 입력한 password

    Raises:

    - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다른 경우
    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND

    Returns:

    - dict: 입력한 정보가 정확하면 access token을 발행한다.
    """
    access_token = user_service.login(
        db,
        email,
        password,
    )
    return {"access_token": access_token, "token_type": "Bearer"}


@router.patch(
    "/password-reset",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    background_tasks: BackgroundTasks,
    email: str = Body(...),
    user_service: UserService = Depends(UserService),
    email_client: EmailClient = Depends(EmailClient),
    db: Session = Depends(db.get_db),
):
    """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

    Args:

    - email: 로그인 시 입력한 이메일 주소

    Raises:

    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 경우에 발생한다.
        - 비밀번호 초기화를 위한 이메일 발송에 실패했을 때 (code: FAILED_TO_SEND_A_MAIL)

    Returns:

    - Message: 비밀번호 초기화 이메일 송신 완료 메세지
    """
    user_service.reset_password(
        db,
        email_client,
        background_tasks,
        email,
    )
    return {"status": "success", "message": "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."}


@router.patch(
    "/password-change",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def change_password(
    password_data: UserPasswordUpdate,
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """임시 비밀번호로 로그인 후, 다른 패스워드로 변경한다.
        기존 패스워드 정보가 현재 로그인된 유저의 패스워드 정보와 일치하면 새로운 패스워드로 변경한다.
        일치하지 않으면 변경하지 않는다.

    Args:

     - password_data (schema.UserPasswordUpdate): 현재 패스워드와 새 패스워드 정보
        - current_password: 현재 패스워드
        - new_password: 새 패스워드

    Raises:

    - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다른 경우
    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND
    - HTTPException (500 INTERNAL SERVER ERROR): 비밀번호 변경에 실패한 경우

     Returns:

     - Message: 실행 완료 메세지
    """
    user_service.change_password(
        db,
        current_user.email,
        **password_data.dict(),
    )
    return {"status": "success", "message": "비밀번호가 변경되었습니다."}


@router.get(
    "/users/current-user/private-data",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
)
def read_private_data(
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """jwt를 사용하여 유저를 인증하고, 로그인한 유저의 상세 정보를 반환한다.

    Raises:

    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND

    Returns:

    - id: 로그인한 유저의 id
    - email: 로그인 시 사용하는 email
    - name: 현재 로그인된 user의 name
    - profile_text: 현재 로그인된 user의 profile text
    """
    return user_service.read_private_data(
        db,
        current_user.email,
    )


@router.get(
    "/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserRead,
    response_model_exclude_unset=True,
)
def read_user(
    user_id: int,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(db.get_db),
) -> UserRead:
    """로그인한 유저 이외의 유저 정보를 조회한다.

    Args:

    - user_id (int): db에 저장된 user id

    Raises:

    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND

    Returns:

    - id: 조회하려는 프로필의 id
    - name: user_id에 해당되는 user의 name
    - profile_text: user_id에 해당되는 user의 profile text
    """
    return user_service.read_user(
        db,
        user_id,
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    data_to_be_updated: UserUpdate,
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> UserRead:
    """user_id와 현재 user id와 같으면 유저 자신의 정보를 수정한다.

    Args:

    - user_id (int): db에 저장된 user id
    - data_to_be_updated (schema.UserUpdate): 업데이트할 user 정보

    Raises:

    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND
    - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 변경에 실패한 경우

    Returns:

    - UserRead: 업데이트된 user 정보를 반환
    """
    updated_user = user_service.update_user(
        db,
        user_id,
        current_user.email,
        data_to_be_updated.dict(exclude_unset=True),
    )
    return updated_user


@router.delete(
    "/users/{user_id}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def delete_user(
    user_id: int,
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
):
    """user_id와 현재 user id와 같으면 유저 자신의 계정을 삭제한다.

    Args:

    - user_id (int): db에 저장된 user id

    Raises:

    - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
    - HTTPException (403 FORBIDDEN): 삭제 권한이 없는 경우
    - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
        - code: USER_NOT_FOUND
    - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 삭제에 실패한 경우

    Returns:

    - Message: 계정 삭제 완료 메세지
    """
    user_service.delete_user(
        db,
        user_id,
        current_user.email,
    )
    return {"status": "success", "message": "계정이 삭제되었습니다."}


@router.get(
    "/users/{user_id}/followers",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_followers(
    user_id: int,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(db.get_db),
) -> List[UserBase]:
    """user_id에 해당하는 유저의 팔로워들을 조회한다.

    Args:

    - user_id (int): user의 id

    Raises:

    - HTTPException (404 NOT FOUND): 팔로워가 없을 때

    Returns:

    - List[UserBase]: 팔로워 목록
    """
    return user_service.get_followers(
        db,
        user_id,
    )


@router.get(
    "/users/{user_id}/followings",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_followings(
    user_id: int,
    user_service: UserService = Depends(UserService),
    db: Session = Depends(db.get_db),
) -> List[UserBase]:
    """user_id에 해당하는 유저의 팔로잉들을 조회한다.

    Args:

    - user_id (int): user의 id

    Raises:

    - HTTPException (404 NOT FOUND): 팔로잉이 없을 때

    Returns:

    - List[UserBase]: 팔로잉 목록
    """
    return user_service.get_followings(
        db,
        user_id,
    )


@router.post(
    "/users/{user_id}/follow",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def follow_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    redis_db: Redis = Depends(redis_db.get_db),
    db: Session = Depends(db.get_db),
) -> Message:
    """현재 로그인한 유저가 user_id에 해당하는 유저를 팔로우한다.

    Args:

    - user_id (int): 팔로우 대상 유저의 id

    Raises:

    - HTTPException (404 NOT FOUND): follower_id에 해당하는 유저가 없을 경우
        - code: USER_NOT_FOUND
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생
        - Follow 관계에 실패한 경우 (code: FAILED_TO_FOLLOW)
        - 알림 생성에 실패한 경우 (code: FAILED_TO_CREATE_NOTIFICATION)

    Returns:

    - Message: 팔로우 성공 메세지
    """
    user_service.follow_user(
        db,
        redis_db,
        background_tasks,
        user_id,
        current_user.id,
    )
    return {"status": "success", "message": "follow 관계 맺기에 성공했습니다."}


@router.post(
    "/users/{user_id}/unfollow",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def unfollow_user(
    user_id: int,
    user_service: UserService = Depends(UserService),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Message:
    """현재 로그인한 유저가 user_id에 해당하는 유저를 언팔로우한다.

    Args:

    - user_id (int): 언팔로우 대상 유저의 id

    Raises:

    - HTTPException (400 BAD REQUEST): 이미 Follow 관계가 취소된 경우
    - HTTPException (404 NOT FOUND): 전달된 정보에 일치하는 Follow 관계를 찾을 수 없을 때
    - HTTPException (500 INTERNAL SERVER ERROR): Follow 관계 끊기에 실패한 경우

    Returns:

    - Message: 언팔로우 성공 메세지
    """
    user_service.unfollow_user(
        db,
        user_id,
        current_user.id,
    )
    return {"status": "success", "message": "follow 관계 취소에 성공했습니다."}
