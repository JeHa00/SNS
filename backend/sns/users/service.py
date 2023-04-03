from datetime import datetime, timedelta
import smtplib
import secrets

from fastapi import Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader
from email.message import EmailMessage
from passlib.context import CryptContext
from jose import jwt, JWTError

from sns.common.config import settings
from sns.common.session import db
from sns.common.path import EMAIL_TEMPLATE_DIR
from sns.users.model import User
from sns.users.schema import UserCreate, Token, UserBase


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/token")


def create_access_token(data: dict, expires: timedelta | None = None) -> str:
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


def get_current_user(
    db: Session = Depends(db.get_db), token: Token = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def get_current_user_verified(current_user: UserBase = Depends(get_current_user)):
    """인증된 현재 유저 정보를 반환한다.

    Args:
        current_user (Annotated[UserBase, Depends): 현재 유저 정보

    Raises:
        HTTPException: 인증되지 않을 경우 발생

    Returns:
        인증된 유저 정보를 반환
    """
    if not is_verified(current_user):
        raise HTTPException(status_code=400, detail="인증되지 않은 유저입니다.")
    return current_user


def send_email(message: EmailMessage, context: dict, template_name: str) -> None:
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


def send_new_account_email(email_to: str, password: str, url: str) -> None:
    """새로운 계정 생성 이메일 메세지를 생성하여 send_email에 전달한다.

    Args:
        email_to (str): 새로 등록한 유저의 이메일
        password (str): 새로 등록한 유저의 패스워드
        url (str): 발송된 이메일에 첨부된 이메일 인증 url
    """
    message = EmailMessage()
    message.add_header("Subject", f"{settings.PJT_NAME} - New account for user")
    message.add_header("From", settings.EMAIL_ADDR)
    message.add_header("To", email_to)
    context = {
        "project_name": settings.PJT_NAME,
        "password": password,
        "email": email_to,
        "link": url,
    }
    data = {"message": message, "context": context, "template_name": "new_account"}
    send_email(**data)


def send_reset_password_email(email_to: str, password: str) -> None:
    """비밀번호 초기화 이메일 메세지를 생성하여 send_email에 전달한다.

    Args:
        email_to (str): 수신자
        password (str): 임시 비밀번호
    """
    message = EmailMessage()
    message.add_header("Subject", f"{settings.PJT_NAME} - Reset password for user")
    message.add_header("From", settings.EMAIL_ADDR)
    message.add_header("To", email_to)
    context = {
        "project_name": settings.PJT_NAME,
        "password": password,
        "email": email_to,
    }
    data = {"message": message, "context": context, "template_name": "reset_password"}
    send_email(**data)


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


def get_user(db: Session, **kwargs) -> User | bool:
    """이메일이 이미 등록되어있는지 또는 해당 이메일을 가진 유저의 비밀번호가 인자로 받은 비밀번호와 일치하는지 판단한다.

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


def create(db: Session, user_info: UserCreate) -> User:
    """받은 정보로 새 유저를 등록한다.

    Args:
        db (Session): db session
        user_info (UserCreate): 새로 등록한 유저의 email과 password

    Returns:
        User: 새로 생성한 유저 객체
    """
    name = secrets.token_urlsafe(8)
    db_obj = User(
        email=user_info.email,
        password=get_password_hash(user_info.password),
        name=f"user-{name}",
        verified=False,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, user: User, user_info: User | dict) -> User:
    """user 정보를 수정한다.

    Args:
        db (Session): db session.
        user (User): user 정보
        user_info (BaseModel | dict): 변경할 유저 정보

    Returns:
        User: _description_
    """
    obj_data = jsonable_encoder(user)
    if isinstance(user_info, dict):
        data_to_be_updated = user_info
    else:
        data_to_be_updated = user_info.dict(exclude_unset=True)
    for field in obj_data:
        if field in data_to_be_updated:
            setattr(user, field, data_to_be_updated[field])
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user_info: User | int) -> User:
    """전달받은 해당 user를 삭제한다.

    Args:
        db (Session): db session
        user_info (BaseModel | int): user model 정보 또는 user.id 정보

    Returns:
        User: 삭제된 user 정보를 반환한다.
    """
    if isinstance(user_info, int):
        user = db.query(User).filter(User.id == id).first()
    else:
        user = user_info
    db.delete(user)
    db.commit()
    return user


def is_verified(user: UserBase | User) -> bool:
    """user의 이메일 인증 여부를 확인한다.

    Args:
        user (User): user 정보

    Returns:
        bool: 인증 여부를 bool 값으로 반환한다.
    """
    return user.verified
