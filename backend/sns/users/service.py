from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import jwt

from sns.common.config import settings
from sns.users.model import User
from sns.users.schema import TokenPayload


class UserService:
    __pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_pwd_context(cls):
        return cls.__pwd_context

    def create_access_token(self, data: dict, expires: timedelta | None = None) -> str:
        """주어진 데이터를 바탕으로 access token을 생성한다.

        Args:
            data (dict): 로그인 시 입력되는 이메일 객체 정보를 의미
            expires (Optional): 토큰 유효기간 정보. Defaults to None.

        Returns:
            Token: 생성된 jwt을 반환한다.
        """
        to_encode = data.copy()
        if expires:
            expire = datetime.utcnow() + expires
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITHM
        )
        return encoded_jwt

    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """plain_password가 hash 화되었을 때 hashed_password와 일치하는지 판단한다.

        Args:
            plain_password (str): 로그인 시 입력하는 패스워드
            hashed_password (str): db에 저장된 해쉬화된 패스워드

        Returns:
            bool: 일치 유무를 반환
        """
        return cls.get_pwd_context().verify(plain_password, hashed_password)

    def get_password_hash(cls, password: str) -> str:
        """암호화된 패스워드를 얻는다.

        Args:
            password (str): 암호화할 패스워드

        Returns:
            str: 암호화된 패스워드
        """
        return cls.get_pwd_context().hash(password)

    def is_verified(self, user: User) -> bool:
        """user의 이메일 인증 여부를 확인한다.

        Args:
            user (User): user 정보

        Returns:
            bool: 인증 여부를 bool 값으로 반환한다.
        """
        return user.verified


user_service = UserService()
