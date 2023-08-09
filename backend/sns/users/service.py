from datetime import datetime, timedelta
import secrets

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from starlette.background import BackgroundTasks
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from sns.common.config import settings
from sns.common.session import db
from sns.users.repositories.email_client import email_client
from sns.users.repositories.db import user_crud
from sns.users.model import User
from sns.users import schema


class UserService:
    __pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    __oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/token")

    def get_pwd_context(
        cls,
    ) -> CryptContext:
        """클래스 변수에 직접 접근하기보다는 클래스 메서드를 통해 pwd_context 를 얻는다.

        Returns:
            CryptContext: 암호화된 패스워드를 얻거나, 암호화된 패스워드와 일반 패스워드의 일치 유무를 확인할 때 사용하기 위해 반환
        """
        return cls.__pwd_context

    def create_access_token(
        self,
        data: dict,
        expires: timedelta | None = None,
    ) -> str:
        """주어진 데이터를 바탕으로 access token을 생성한다.

        Args:
            data (dict): 로그인 시 입력되는 이메일 객체 정보를 의미
            expires (Optional): 토큰 유효기간 정보. Defaults to None.

        Returns:
            Token: 생성된 jwt을 반환
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
            plain_password (str): 로그인 시 입력하는 패스워드
            hashed_password (str): db에 저장된 해쉬화된 패스워드

        Raises:
            HTTPException (400 BAD REQUEST): 일치하지 않을 경우 발생하는 에러

        Returns:
            bool: 일치 유무를 반환
        """
        if cls.get_pwd_context().verify(
            plain_password,
            hashed_password,
        ):
            return True
        else:
            raise HTTPException(
                status_code=400,
                detail="입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다.",
            )

    def get_password_hash(
        cls,
        password: str,
    ) -> str:
        """암호화된 패스워드를 얻는다.

        Args:
            password (str): 암호화할 패스워드

        Returns:
            str: 암호화된 패스워드
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
            user (User): user 정보

        Raises:
            HTTPException (403 FORBIDDEN): 이메일 미인증일 경우 발생하는 에러

        Returns:
            bool: user의 verified 값
        """
        if not user.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요.",
            )

        return user.verified

    def send_verification_email(
        self,
        db: Session,
        email: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """입력 받은 email 주소로 이메일 인증 메일을 보낸다.

        Args:
            email (str): 회원가입 시 입력한 이메일 주소로, 이 이메일 주소로 인증 메일을 발송한다.
            db (Session): db session

        Raises:
            HTTPException (500): 이메일 전송과정에서 문제 발생 시 등록한 유저 삭제와 에러를 일으킨다.
        """
        try:
            code = secrets.token_urlsafe(10)  # verification_code의 최소 길이 10
            new_user = self.get_user(
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
            data = {"email_to": email, "url": url}
            background_tasks.add_task(email_client.send_new_account_email, **data)
        except Exception:
            user_crud.remove(
                db,
                new_user,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이메일 발송 과정에서 에러가 발생했습니다. 다시 회원가입 정보를 입력하세요",
            )

    def send_password_reset_email(
        self,
        db: Session,
        email: str,
        background_tasks: BackgroundTasks,
    ) -> None:
        """입력 받은 email 주소로 임시 비밀번호를 발송한다.

        Args:
            email (str): 회원가입 시 입력한 이메일 주소로, 이 이메일 주소로 임시 비밀번호를 받는다.
            db (Session): db session

        Raises:
            HTTPException (500 INTERNAL SERVER ERROR): 이메일 전송과정에서 문제가 생기면 에러를 발생시킨다.
        """
        try:
            temporary_password = secrets.token_urlsafe(8)  # 패스워드의 최소 길이 8
            selected_user = self.get_user(
                db,
                email=email,
            )
            hashed_password = self.get_password_hash(temporary_password)

            self.update(
                db,
                user=selected_user,
                data_to_be_updated={"password": hashed_password},
            )

            data = {"email_to": email, "password": temporary_password}
            background_tasks.add_task(
                email_client.send_reset_password_email,
                **data,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이메일 발송 과정에서 에러가 발생했습니다. 다시 시도하세요.",
            )

    @staticmethod
    def get_current_user(
        db: Session = Depends(db.get_db),
        token: schema.Token = Depends(__oauth2_scheme),
    ) -> User:
        """발급했던 Token으로부터 user 정보를 가져온다.

        Args:
            db (Session): db session
            token (Token, optional): 발급받은 token 정보

        Raises:
            credentials_exception: decoding 작업 시 발생되는 JWT error
            credentials_exception: jwt로부터 얻은 email 정보로 유저 조회 시 없을 경우 발생되는 에러

        Returns:
            User: jwt로부터 얻은 유저 정보
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
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = user_crud.get_user(
            db,
            email=email,
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
            current_user (Depends): 현재 유저 정보

        Raises:
            HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생

        Returns:
            str: 인증된 user의 email 정보
        """

        if not current_user.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요.",
            )

        return current_user

    def check_if_user_is_none(self, user: User) -> None:
        """반환된 user 정보가 None이면 404 status error를 발생시킨다.

        Args:
            user (User): user 정보가 존재하는지 판단

        Raises:
            HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        """
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="해당되는 유저를 찾을 수 없습니다.",
            )

    def get_user(
        self,
        db: Session,
        email: str = None,
        user_id: int = None,
        verification_code: str = None,
        password: str = None,
    ) -> User:
        """입력 받은 정보를 UserDB class에 전달하여 유저 정보를 조회한다.
            email, user_id, verification_code 중 하나의 정보를 받으면 이 정보를 토대로 유저 정보를 조회한다.
            추가로 password 정보까지 포함하여 2개의 key 값을 입력받을 경우,
            위 3가지 정보를 토대로 조회된 user가 해당 password 정보를 가지고 있는지 확인한다.

        Args:
            - db (Session): db session
            - email: email 정보
            - user_id: user id 정보
            - verification_code: 인증 코드 정보
            - password: user의 password 정보

        Returns:
            - User: 조회된 user 객체
        """

        # 받은 정보를 통해 user 조회
        if email is not None:
            user = user_crud.get_user(
                db,
                email=email,
            )
        elif user_id is not None:
            user = user_crud.get_user(
                db,
                user_id=user_id,
            )
        else:
            user = user_crud.get_user(
                db,
                verification_code=verification_code,
            )

        if password is not None:
            # 조회된 user의 비밀번호 정보와 입력받은 password 정보와 일치하는지 확인
            if self.verify_password(
                password,
                user.password,
            ):
                return user
        else:
            return user

    def create(
        self,
        db: Session,
        data_for_signup: dict,
    ) -> User:
        """data_for_signup로 받은 정보를 UserDB class에 전달하여 새로운 user를 생성한다.
            user 생성 시 패스워드는 암호화하여 저장하기 위해 암호화된 패스워드로 변경한 후 infrastructure layer에 전달한다.

        Args:
            db (Session): db session
            data_for_signup (schema.UserCreate): 등록할 user의 가입 정보

        Raises:
            HTTPException (500 INTERNAL SERVER ERROR): user 등록 과정에서 문제가 생기면 에러를 발생시킨다.

        Returns:
            User: 생성된 user 객체
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
            db (Session): db session
            user (User): user 정보
            data_to_be_updated (dict): 해당 user의 변경될 정보

        Raises:
            HTTPException (500): user 정보 변경 과정에서 문제가 생기면 에러를 발생시킨다.

        Returns:
            User: 수정된 user 객체
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
            db (Session): db session
            user_to_be_deleted (User | int): 삭제될 user 정보

        Raises:
            HTTPException (500): user 정보 삭제 과정에서 문제가 생기면 에러를 발생시킨다.

        Returns:
            dict: 작업 성공 메세지
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
        background_tasks: BackgroundTasks,
        data_for_signup: dict,
    ) -> None:
        """email과 password로 새 user를 등록한다.

        Args:

        - data_for_signup (schema.UserCreate) : 등록할 email과 password 정보

        Raises:

        - HTTPException (400 BAD REQUEST): 이미 인증된 이메일인 경우
        - HTTPException (403 FORBIDDEN): 등록은 되었지만 이메일 미인증일 경우
        - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생한다.
            - 유저 생성에 실패했을 때
            - 이메일 인증을 위한 이메일 발송에 실패했을 때
        """
        user = self.get_user(
            db,
            email=data_for_signup.get("email"),
        )

        if user and self.is_verified(user):
            raise HTTPException(
                status_code=400,
                detail="이미 인증된 이메일입니다.",
            )

        self.create(
            db,
            data_for_signup,
        )  # 미인증 유저 생성

        # 이메일 인증 메일 발송하기
        self.send_verification_email(
            db,
            email=data_for_signup.get("email"),
            background_tasks=background_tasks,
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
                - verification code가 code 값과 일치하는 user를 찾지 못할 때 발생한다.
            - HTTPException (500 INTERNAL SERVER ERROR): 인증 상태값 변경에 실패했을 때 발생한다.
        """
        user = self.get_user(
            db,
            verification_code=code,
        )

        self.check_if_user_is_none(user)

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

        - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다를 때 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        - HTTPException (403 FORBIDDEN): 등록은 했지만 이메일 인증이 완료되지 못한 계정일 때 발생

        Returns:

        - str: 생성된 access token을 반환
        """
        user = self.get_user(
            db,
            email=email,
            password=password,
        )

        self.check_if_user_is_none(user)

        if self.is_verified(user):
            access_token = self.create_access_token({"sub": email})
            return access_token

    def reset_password(
        self,
        db: Session,
        email: str,
        background_task: BackgroundTasks,
    ) -> None:
        """로그인 시 비밀번호를 잊었을 때, 입력한 이메일 주소로 임시 비밀번호를 보낸다.

        Args:

        - email: 로그인 시 입력한 이메일 주소

        Raises:

        - HTTPException (403 FORBIDDEN): 등록은 했지만 이메일 인증이 완료되지 못한 계정일 때 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        - HTTPException (500 INTERNAL SERVER ERROR): 다음 경우에 발생한다.
            - 비밀번호 초기화를 위한 이메일 발송에 실패했을 때
        """
        user = self.get_user(
            db,
            email=email,
        )

        self.check_if_user_is_none(user)

        if self.is_verified(user):
            self.send_password_reset_email(
                db,
                email,
                background_task,
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

        - HTTPException (400 BAD REQUEST): 입력한 비밀번호가 회원가입 시 입력한 비밀번호와 다를 때 발생
        - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        - HTTPException (500 INTERNAL SERVER ERROR): 비밀번호 변경에 실패했을 때 발생한다.
        """
        user = self.get_user(
            db,
            email=email,
        )

        self.check_if_user_is_none(user)

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

    def read_user(
        self,
        db: Session,
        user_id: int,
        email: str,
    ) -> schema.UserRead:
        """user_id가 current_user와의 일치 유무에 따라 다른 user 정보를 반환한다.
        - user_id가 current_user와 동일하면 email을 포함한 current_user의 정보를 전달한다.
        - user_id와 current_user가 다르면 user_id에 해당되는 name과 profile text를 전달한다.


        Args:

        - user_id (int): db에 저장된 user id
        - email (str): 유저의 email 정보

        Raises:

        - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생

        Returns:

        - User or dict: 유저 정보
        """
        selected_user = self.get_user(
            db,
            user_id=user_id,
        )

        self.check_if_user_is_none(selected_user)

        if selected_user:
            if selected_user.email == email:
                return schema.UserRead(
                    email=selected_user.email,
                    name=selected_user.name,
                    profile_text=selected_user.profile_text,
                )
            else:
                return schema.UserRead(
                    name=selected_user.name,
                    profile_text=selected_user.profile_text,
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

        - HTTPException (401 UNAUTHORIZED): 변경 권한이 없음을 나타내는 에러
        - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 변경에 실패했을 때 발생

        Returns:

        - User: 변경된 user 정보를 반환
        """
        selected_user = self.get_user(
            db,
            user_id=user_id,
        )

        self.check_if_user_is_none(selected_user)

        if selected_user.email == email:
            updated_user = self.update(
                db,
                selected_user,
                data_to_be_updated,
            )
            return updated_user
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
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

        - HTTPException (401 UNAUTHORIZED): 삭제 권한이 없음을 나타내는 에러
        - HTTPException (403 FORBIDDEN): user가 이메일 인증이 완료되지 않으면 발생
        - HTTPException (404 NOT FOUND): email에 해당하는 user를 찾지 못할 때 발생
        - HTTPException (500 INTERNAL SERVER ERROR): 유저 정보 삭제에 실패했을 때 발생
        """
        selected_user = self.get_user(
            db,
            user_id=user_id,
        )

        self.check_if_user_is_none(selected_user)

        if selected_user.email == email:
            self.remove(
                db,
                selected_user,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="삭제할 권한이 없습니다.",
            )


user_service = UserService()
