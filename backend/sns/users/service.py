from datetime import datetime, timedelta
from typing import List
import secrets

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from starlette.background import BackgroundTasks
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from redis.client import Redis
from jose import jwt, JWTError

from sns.common.http_exceptions import CommonHTTPExceptions
from sns.common.config import settings
from sns.common.session import db
from sns.users.repositories.email_client import EmailClient
from sns.users.repositories.db import user_crud
from sns.users.model import User, Follow
from sns.users import schema
from sns.notifications.repository import notification_crud, RedisQueue
from sns.notifications.schema import FollowNotificationData


class UserService:
    __pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    __oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/token")

    ERROR_TO_SEND_A_EMAIL = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "code": "FAILED_TO_SEND_A_EMAIL",
            "message": "이메일 발송 과정에서 에러가 발생했습니다. 다시 시도하세요.",
        },
    )

    def get_pwd_context(
        cls,
    ) -> CryptContext:
        """클래스 변수에 직접 접근하기보다는 클래스 메서드를 통해 pwd_context 를 얻는다.

        Returns:
            - CryptContext: 암호화된 패스워드를 얻거나, 암호화된 패스워드와 일반 패스워드의 일치 유무를 확인할 때 사용하기 위해 반환
        """
        return cls.__pwd_context

    def create_access_token(
        self,
        data: dict,
        expires: timedelta | None = None,
    ) -> str:
        """주어진 데이터를 바탕으로 access token을 생성한다.

        Args:
            - data (dict): 로그인 시 입력되는 이메일 객체 정보를 의미
            - expires (Optional): 토큰 유효기간 정보. Defaults to None.

        Returns:
            - Token: 생성된 jwt을 반환
        """
        to_encode = data.copy()
        if expires:
            expire = datetime.utcnow() + expires
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.SECRET_ALGORITHM,
        )
        return encoded_jwt

    def verify_password(
        cls,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """plain_password가 암호화되었을 때 hashed_password와 일치하는지 판단한다.

        Args:
            - plain_password (str): 로그인 시 입력하는 패스워드
            - hashed_password (str): db에 저장된 해쉬화된 패스워드

        Raises:
            - HTTPException (400 BAD REQUEST): 일치하지 않을 경우 발생하는 에러

        Returns:
            - bool: 일치 유무를 반환
        """
        if cls.get_pwd_context().verify(
            plain_password,
            hashed_password,
        ):
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다.",
            )

    def get_password_hash(
        cls,
        password: str,
    ) -> str:
        """암호화된 패스워드를 얻는다.

        Args:
            - password (str): 암호화할 패스워드

        Returns:
            - str: 암호화된 패스워드
        """
        return cls.get_pwd_context().hash(
            password,
        )

    def is_verified(
        self,
        user: User,
    ) -> bool:
        """user의 이메일 인증 여부를 확인한다.

        Args:
            - user (User): user 정보

        Raises:
            - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우

        Returns:
            - bool: user의 verified 값
        """
        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요.",
            )

        return user.verified

    def send_verification_email(
        self,
        db: Session,
        email_client: EmailClient,
        background_tasks: BackgroundTasks,
        email: str,
    ) -> None:
        """입력 받은 email 주소로 이메일 인증 메일을 보낸다.

        Args:
            - db (Session): db session
            - email (str): 회원가입 시 입력한 이메일 주소

        Raises:
            - HTTPException (500): 이메일 전송과정에서 문제 발생 시 등록한 유저 삭제와 에러를 일으킨다.
                - code: FAILED_TO_SEND_A_MAIL
        """
        try:
            code = secrets.token_urlsafe(10)  # verification_code의 최소 길이 10

            new_user = user_crud.get_user(
                db,
                email=email,
            )

            self.update(
                db,
                user=new_user,
                data_to_be_updated={"verification_code": code},
            )

            url = (
                f"http://0.0.0.0:8000{settings.API_V1_PREFIX}/verification-email/{code}"
            )

            background_tasks.add_task(
                email_client.send_new_account_email,
                email,
                url,
            )
        except Exception:
            user_crud.remove(db, new_user)

            raise self.ERROR_TO_SEND_A_EMAIL

    def send_password_reset_email(
        self,
        db: Session,
        email_client: EmailClient,
        background_tasks: BackgroundTasks,
        email: str,
    ) -> None:
        """입력 받은 email 주소로 임시 비밀번호를 발송한다.

        Args:
            - db (Session): db session
            - email (str): 회원가입 시 입력한 이메일 주소

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): 이메일 전송과정에서 문제가 생기면 에러를 발생시킨다.
                - code: FAILED_TO_SEND_A_MAIL
        """
        try:
            temporary_password = secrets.token_urlsafe(8)  # 패스워드의 최소 길이 8
            selected_user = user_crud.get_user(
                db,
                email=email,
            )
            hashed_password = self.get_password_hash(temporary_password)

            self.update(
                db,
                user=selected_user,
                data_to_be_updated={"password": hashed_password},
            )

            background_tasks.add_task(
                email_client.send_password_reset_email,
                email,
                temporary_password,
            )
        except Exception:
            raise self.ERROR_TO_SEND_A_EMAIL

    @staticmethod
    def get_current_user(
        db: Session = Depends(db.get_db),
        token: schema.Token = Depends(__oauth2_scheme),
    ) -> User:
        """발급했던 Token으로부터 user 정보를 가져온다.

        Args:
            - db (Session): db session
            - token (Token, optional): 발급받은 token 정보

        Raises:
            - HTTPException (401 UNAUTHORIZED): 다음 두 가지 경우에 발생한다.
                - decoding 작업 시 발생되는 JWT error
                - jwt로부터 얻은 email 정보로 유저 조회 시 없을 경우 발생되는 에러

        Returns:
            - User: jwt로부터 얻은 유저 정보
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                settings.SECRET_ALGORITHM,
            )
            name: str = payload.get("sub")
            if name is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = user_crud.get_user(
            db,
            name=name,
        )

        if user is None:
            raise credentials_exception

        return user

    @staticmethod
    def get_current_user_verified(
        current_user: User = Depends(get_current_user),
    ) -> str:
        """인증된 현재 유저 정보를 반환한다.

        Args:
           - current_user (Depends): 현재 유저 정보

        Raises:
            - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우

        Returns:
           - str: 인증된 user의 email 정보
        """

        if not current_user.verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요.",
            )

        return current_user

    def create(
        self,
        db: Session,
        data_for_signup: dict,
    ) -> User:
        """data_for_signup로 받은 정보를 UserDB class에 전달하여 새로운 user를 생성한다.
            user 생성 시 패스워드는 암호화하여 저장하기 위해 암호화된 패스워드로 변경한 후 infrastructure layer에 전달한다.

        Args:
            - db (Session): db session
            - data_for_signup (schema.UserCreate): 등록할 user의 가입 정보

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): user 등록 과정에서 문제가 생기면 에러를 발생시킨다.
                - code: FAILED_TO_CREATE

        Returns:
            - User: 생성된 user 객체
        """
        # password 암호화
        data_for_signup["password"] = self.get_password_hash(
            data_for_signup.get("password"),
        )

        data_for_signup.pop("password_confirm")  # password_confirm key 제거
        data_for_signup[
            "name"
        ] = f"user-{secrets.token_urlsafe(8)}"  # minimum name length

        try:
            new_user = user_crud.create(db, **data_for_signup)
            return new_user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 생성에 실패했습니다.",
            )

    def update(
        self,
        db: Session,
        user: User,
        data_to_be_updated: dict,
    ) -> User:
        """user 정보와 업데이트할 정보를 UserDB class에 전달하여 해당 user 정보를 수정한다.

        Args:
            - db (Session): db session
            - user (User): user 정보
            - data_to_be_updated (dict): 해당 user의 변경될 정보

        Raises:
            - HTTPException (500): user 정보 변경 과정에서 문제가 발생할 경우

        Returns:
            - User: 수정된 user 객체
        """
        try:
            updated_user = user_crud.update(
                db,
                user,
                **data_to_be_updated,
            )
            return updated_user
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 정보 변경에 실패하였습니다.",
            )

    def remove(
        self,
        db: Session,
        user_to_be_deleted: User | int,
    ) -> dict:
        """삭제할 user의 id 또는 User 객체 정보를 UserDB class에 전달하여 해당 user 정보를 삭제한다.

        Args:
            - db (Session): db session
            - user_to_be_deleted (User | int): 삭제될 user 정보

        Raises:
            - HTTPException (500): user 정보 삭제 과정에서 문제가 생기면 에러를 발생시킨다.

        Returns:
            - dict: 작업 성공 메세지
        """
        try:
            user_crud.remove(
                db,
                user_to_be_deleted=user_to_be_deleted,
            )
            return {"status": "success"}
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="계정 삭제를 실패하였습니다.",
            )

    def signup(
        self,
        db: Session,
        email_client: EmailClient,
        background_tasks: BackgroundTasks,
        data_for_signup: dict,
    ) -> None:
        """email과 password로 새 user를 등록한다.

        Args:
            - data_for_signup (schema.UserCreate) : 등록할 email과 password 정보

        Raises:
            - HTTPException (400 BAD REQUEST): 이미 인증된 이메일인 경우
            - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
            - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생한다.
                - 유저 생성에 실패할 경우 (code: FAILED_TO_CREATE)
                - 이메일 인증을 위한 이메일 발송에 실패할 경우 (code: FAILED_TO_SEND_A_EMAIL)
        """
        user = user_crud.get_user(
            db,
            email=data_for_signup.get("email"),
        )

        if user and self.is_verified(user):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 인증된 이메일입니다.",
            )

        # 미인증 유저 생성
        self.create(
            db,
            data_for_signup,
        )

        # 이메일 인증 메일 발송하기
        self.send_verification_email(
            db,
            email_client,
            background_tasks,
            data_for_signup.get("email"),
        )

    def verify_email(
        self,
        db: Session,
        code: str,
    ) -> None:
        """code 정보를 받아 user를 조회하여 해당 user의 인증 상태를 True로 바꾼다.

        Args:
            - code (str) : url에 담겨진 인증 code 정보

        Raises:
            - HTTPException (404 NOT FOUND): 다음 경우에 발생한다.
                - verification code가 code 값과 일치하는 user를 찾지 못한 경우
                    - code: USER_NOT_FOUND
            - HTTPException (500 INTERNAL SERVER ERROR): 인증 상태값 변경에 실패한 경우
        """
        user = user_crud.get_user(
            db,
            verification_code=code,
        )

        if not user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        self.update(
            db,
            user=user,
            data_to_be_updated={"verified": True},
        )

    def login(
        self,
        db: Session,
        email: str,
        password: str,
    ) -> str:
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

        - str: 생성된 access token을 반환
        """
        user = user_crud.get_user(
            db,
            email=email,
        )

        if not user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        self.verify_password(password, user.password)

        if self.is_verified(user):
            return self.create_access_token({"sub": user.name})  # access token 반환

    def reset_password(
        self,
        db: Session,
        email_client: EmailClient,
        background_task: BackgroundTasks,
        email: str,
    ) -> None:
        """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

        Args:

        - email: 로그인 시 입력한 이메일 주소

        Raises:

        - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
            - code: USER_NOT_FOUND
        - HTTPException (500 INTERNAL SERVER ERROR): 다음 경우에 발생한다.
            - 비밀번호 초기화를 위한 이메일 발송에 실패했을 때 (code: FAILED_TO_SEND_A_MAIL)
        """
        user = user_crud.get_user(
            db,
            email=email,
        )

        if not user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        if self.is_verified(user):
            self.send_password_reset_email(
                db,
                email_client,
                background_task,
                email,
            )

    def change_password(
        self,
        db: Session,
        email: str,
        current_password: str,
        new_password: str,
    ) -> None:
        """임시 비밀번호로 로그인 후, 다른 패스워드로 변경한다.
            기존 패스워드 정보가 현재 유저의 패스워드 정보와 일치하면 새로운 패스워드로 변경한다.
            일치하지 않으면 변경하지 않는다.

        Args:

        - email (str): 유저의 email 정보
        - current_password: 현재 패스워드
        - new_password: 새 패스워드

        Raises:

        - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다른 경우
        - HTTPException (401 UNAUTHORIZED): 등록은 되었지만 이메일 인증이 미완료 상태인 경우
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못한 경우
            - USER_NOT_FOUND
        - HTTPException (500 INTERNAL SERVER ERROR): 비밀번호 변경에 실패한 경우
        """
        user = user_crud.get_user(
            db,
            email=email,
        )

        if not user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        if self.verify_password(
            current_password,
            user.password,
        ):
            hashed_password = self.get_password_hash(new_password)
            self.update(
                db,
                user,
                {"password": hashed_password},
            )

    def read_private_data(
        self,
        db: Session,
        current_user_id: int,
    ) -> User:
        """로그인한 유저 이외의 유저 프로필 정보를 조회한다.

        Args:

        - current_user_id (int): 현재 로그인한 유저의 id

        Returns:

        - User: 조회된 유저 정보
        """
        selected_user = user_crud.get_user(
            db,
            user_id=current_user_id,
        )

        if not selected_user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        return selected_user

    def read_user(
        self,
        db: Session,
        current_user_id: int,
        user_id: int,
    ) -> schema.UserReadWithFollowed:
        """로그인한 유저 이외의 유저 프로필 정보를 조회한다.

        Args:

        - user_id (int): db에 저장된 user id

        Raises:

        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
            - code: USER_NOT_FOUND

        Returns:

        - schema.UserReadWithFollowed
            - id: 조회하려는 프로필의 id
            - name: user_id에 해당되는 user의 name
            - profile_text: user_id에 해당되는 user의 profile text
            - followed: user_id와 현재 로그인한 유저의 팔로우 유무
        """
        selected_user = user_crud.get_user(
            db,
            user_id=user_id,
        )

        selected_follow = user_crud.get_follow(
            db,
            following_id=current_user_id,
            follower_id=user_id,
        )

        if not selected_user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        return schema.UserReadWithFollowed(
            id=selected_user.id,
            name=selected_user.name,
            profile_text=selected_user.profile_text,
            followed=selected_follow.is_followed if selected_follow else False,
        )

    def update_user(
        self,
        db: Session,
        user_id: int,
        email: str,
        data_to_be_updated: dict,
    ) -> User:
        """user_id와 현재 user id와 같으면 유저 자신의 정보를 수정한다.

        Args:

        - user_id (int): db에 저장된 user id
        - email (str): token에서 가져온 현재 유저의 email 정보
        - data_to_be_updated (dict): 업데이트할 user 정보

        Raises:

        - HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
            - code: USER_NOT_FOUND
        - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 변경에 실패한 경우

        Returns:

        - User: 변경된 user 정보를 반환
        """
        selected_user = user_crud.get_user(
            db,
            user_id=user_id,
        )

        if not selected_user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        if selected_user.email == email:
            return self.update(
                db,
                selected_user,
                data_to_be_updated,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="수정할 권한이 없습니다.",
            )

    def delete_user(
        self,
        db: Session,
        user_id: int,
        email: str,
    ) -> None:
        """user_id와 현재 user id와 같으면 유저 자신의 계정을 삭제한다.

        Args:

        - user_id (int): db에 저장된 user id
        - email (str): 유저의 이메일 정보

        Raises:

        - HTTPException (403 FORBIDDEN): 삭제 권한이 없는 경우
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
            - code: USER_NOT_FOUND
        - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 삭제에 실패한 경우
        """
        selected_user = user_crud.get_user(
            db,
            user_id=user_id,
        )

        if not selected_user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        if selected_user.email == email:
            self.remove(
                db,
                selected_user,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="삭제할 권한이 없습니다.",
            )

    def get_followers(
        self,
        db: Session,
        following_id: int,
    ) -> List[User]:
        """following_id에 해당하는 유저의 팔로워들을 조회한다.
        팔로워가 없으면 빈 리스트를 반환한다.

        Args:

        - following_id (int): user의 id

        Returns:

        - List[User]: 팔로워 목록
        """
        return user_crud.get_followers(db, following_id)

    def get_followings(
        self,
        db: Session,
        follower_id: int,
    ) -> List[User]:
        """follower_id에 해당하는 유저를 따르는 팔로잉들을 조회한다.
        팔로잉이 존재하지 않으면 빈 리스트를 반환한다.

        Args:

        - follower_id (int): 유저의 id

        Returns:

        - List[User]: 팔로잉 목록
        """
        return user_crud.get_followings(db, follower_id)

    def follow_user(
        self,
        db: Session,
        redis_db: Redis,
        background_tasks: BackgroundTasks,
        follower_id: int,
        following_id: int,
    ) -> bool:
        """주어진 정보를 바탕으로 follow 관계를 맺는다.
            주어진 정보를 바탕으로 Follow 객체가 이미 존재하는지 조회 후,
            조회된 Follow 객체의 is_followed 값이 False이면 True롤 변경한다.
            조회 후 없다면 새로 생성한다.
            follower_id는 팔로우를 당하는 유저의 id, following_id는 팔로우를 거는 유저의 id 를 말한다.

        Args:

        - follower_id (int): 팔로우를 당하는 유저의 id
        - following_id (int): 팔로우를 거는 유저의 id

        Raises:

        - HTTPException (404 NOT FOUND): follower_id에 해당하는 유저가 없을 경우
            - code: USER_NOT_FOUND
        - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생
            - Follow 관계에 실패한 경우 (code: FAILED_TO_FOLLOW)
            - 알림 생성에 실패한 경우 (code: FAILED_TO_CREATE_NOTIFICATION)

        Returns:
        - bool: follow 관계 맺기 성공 시 True를 반환, 실패 시 에러를 발생
        """
        follower = user_crud.get_user(db, user_id=follower_id)

        if not follower:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        try:
            follow = user_crud.follow(
                db,
                follower_id,
                following_id,
            )

            background_tasks.add_task(
                self.create_and_add_notification,
                db,
                redis_db,
                follow,
            )

            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FAILED_TO_FOLLOW",
                    "detail": "follow 관계를 맺는데 실패하였습니다.",
                },
            )

    def unfollow_user(
        self,
        db: Session,
        follower_id: int,
        following_id: int,
    ) -> bool:
        """주어진 정보를 바탕으로 follow 관계를 끊는다.
            주어진 정보의를 바탕으로 Follow 객체를 조회 후, 해당 객체의 is_followed 값이 False이면 에러를 발생시킨다.
            True이면 언팔로우를 시도한다.
            follower_id는 팔로우를 당하는 유저의 id, following_id는 팔로우를 거는 유저의 id 를 말한다.

        Args:

        - follower_id (int): 팔로우를 당했던 유저의 id
        - following_id (int): 팔로우를 걸었던 유저의 id

        Raises:

        - HTTPException (400 BAD REQUEST): 이미 Follow 관계가 취소된 경우
        - HTTPException (404 NOT FOUND): 전달된 정보에 일치하는 Follow 관계를 찾을 수 없을 때
        - HTTPException (500 INTERNAL SERVER ERROR): Follow 관계 끊기에 실패한 경우

        Returns:

        - bool: follow 관계 끊기 성공 시 True를 반환
        """
        selected_follow = user_crud.get_follow(db, follower_id, following_id)

        if not selected_follow:
            raise HTTPException(
                status_code=404,
                detail="해당 정보에 일치하는 Follow 관계를 찾을 수 없습니다.",
            )

        try:
            user_crud.unfollow(db, selected_follow)
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="follow 관계 취소가 실패하였습니다.",
            )

    def find_users(
        self,
        db: Session,
        name: str,
        page: int,
    ) -> List[User]:
        """해당 name을 가지고 있는 유저들을 조회한다.

        Args:
            db (Session): db session
            name (str): 조회할 유저의 name
            page (int): 조회할 page 번호. 페이지당 조회되는 user 수는 10명

        Returns:
            List[User]: 조회된 유저 목록
        """

        users_per_a_page = 10

        return user_crud.get_users_by_name(db, name, skip=page * users_per_a_page)

    def create_and_add_notification(
        self,
        db: Session,
        redis_db: Redis,
        new_follow: Follow,
    ) -> bool:
        """주어진 데이터를 가지고 알림을 생성하고, message queue에 추가한다.
        follower_id를 통해서 follower의 email 정보를 얻은 후, 이 정보를 queue의 key값으로 사용하여 queue를 생성한다.
        그리고 이 queue에 bytestr 타입으로 follow event data를 추가한다.

        Args:

        - db (Session): mysql db session
        - redis_db (Redis): message queue에 접속하는 db
        - message_queue (RedisQueue): redis_db를 통해 생성되는 message_queue
        - new_follow (Follow): 새로 생성된 follow 객체

        Raises:

        - HTTPException (500 INTERNAL SERVER ERROR): 알림 생성에 실패한 경우
            - code: FAILED_TO_CREATE_NOTIFICATION

        Returns:

        - bool : 성공 시 True를 반환
        """

        try:
            new_notification = notification_crud.create_notification_on_follow(
                db,
                new_follow.id,
                new_follow.follower_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FAILED_TO_CREATE_NOTIFICATION",
                    "detail": "알림 생성에 실패했습니다.",
                },
            )

        notification_data = FollowNotificationData(
            type=new_notification.type,
            notification_id=new_notification.id,
            notified_user_id=new_follow.follower_id,
            following_id=new_follow.following_id,
            created_at=str(new_notification.created_at),
        )

        # message_queue 초기화 및 알림 데이터 추가
        follower = user_crud.get_user(db, user_id=new_follow.follower_id)

        message_queue = RedisQueue(
            redis_db,
            f"notification_useremail:{follower.email}",
        )

        message_queue.push(notification_data.dict())

        return True


user_service = UserService()
