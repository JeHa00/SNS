from datetime import datetime, timedelta
from typing import Optional
import smtplib

from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt

from sns.common.config import settings
from sns.common.path import EMAIL_TEMPLATE_DIR
from sns.users.model import User
from sns.users.schema import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# access_token 생성
def create_access_token(data: dict, expires: Optional[timedelta] = None):
    """주어진 데이터를 바탕으로 access token을 생성한다.

    Args:
        data (dict): 로그인 시 입력되는 이메일 객체 정보를 의미
        expires (Optional): 토큰 유효기간 정보. Defaults to None.

    Returns:
        Token: 생성된 jwt을 반환한다.
    """
    if expires:
        expire = datetime.utcnow() + expires
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(data)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.SECRET_ALGORITHM
    )
    return encoded_jwt


# email 관련
def send_email(message: EmailMessage, context: dict, template_name: str):
    """email message를 받아 해당 정보로 발송한다.

    Args:
        message (EmailMessage): email이 발신자, 수신자, 제목 정보
        context (dict): template_name을 가진 email template을 렌더링하기 위해 전달되는 값
        template_name (str): 무슨 email template을 사용할지를 결정한다.
    """
    env = Environment(loader=FileSystemLoader(EMAIL_TEMPLATE_DIR))
    template = env.get_template(f"{template_name}.html")
    message.set_content(template.render(**context), subtype="html")
    with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(settings.EMAIL_ADDR, settings.EMAIL_PASSWORD)
        smtp.send_message(message)


def send_new_account_email(email_to: str, password: str):
    """새로운 계정 생성 이메일 메세지를 생성하여 send_email에 전달한다.

    Args:
        email_to (str): 새로 등록한 유저의 이메일
        password (str): 새로 등록한 유저의 패스워드
    """
    message = EmailMessage()
    message.add_header("Subject", f"{settings.PJT_NAME} - New account for user")
    message.add_header("From", settings.EMAIL_ADDR)
    message.add_header("To", email_to)
    context = {
        "project_name": settings.PJT_NAME,
        "password": password,
        "email": email_to,
    }
    data = {"message": message, "context": context, "template_name": "new_account"}
    send_email(**data)


# password 관련
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """plain_password가 hash 화되었을 때 hashed_password와 일치하는지 판단한다.

    Args:
        plain_password (str): 로그인 시 입력하는 패스워드
        hashed_password (str): db에 저장된 해쉬화된 패스워드

    Returns:
        bool: 일치 유무를 반환
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """암호화된 패스워드를 얻는다.

    Args:
        password (str): 암호화할 패스워드

    Returns:
        str: 암호화된 패스워드
    """
    return pwd_context.hash(password)


# user 생성 로직
def get_user(db: Session, **kwargs) -> User:
    """이메일이 이미 등록되어있는지 또는 해당 이메일을 가진 유저의 비밀번호가 인자로 받은 비밀번호와 일치하는지 판단

    Args:
        - db (Session): 연결된 db

    Kwargs:
        - email: 등록 유무를 확인하려는 이메일
        - password: 등록된 이메일을 가진 유저의 패스워드인지 확인하려는 패스워드

    Returns:
        User: 입력된 값들과 일치하는 유저 객체를 반환한다. 없으면 None을 반환
    """
    user = db.query(User).filter(User.email == kwargs["email"]).first()
    if len(kwargs) == 1:
        return user
    else:
        if not user or not verify_password(kwargs["password"], user.password):
            return False
        return user


def create_user(user_info: UserCreate, db: Session) -> User:
    """받은 정보로 새 유저를 등록한다.

    Args:
        user_info (UserCreate): 새로 등록한 유저의 email과 password
        db (Session): db session

    Returns:
        User: 새로 생성한 유저 객체
    """
    db_obj = User(
        email=user_info.email,
        hashed_password=get_password_hash(user_info.password),
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


# Token으로부터 user 정보 얻기

# user 1명 조회 로직

# user 다수 조회 로직

# user 업데이트 로직

# user 삭제 로직
