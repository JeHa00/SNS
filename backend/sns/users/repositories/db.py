import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from sns.common.config import settings
from sns.common.session import db
from sns.users.service import user_service
from sns.users import schema
from sns.users.model import User, Follow


class UserDB:
    __oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/token")

    def get_user(self, db: Session, **kwargs) -> User | bool:
        """이메일이 이미 등록되어있는지 또는 해당 이메일을 가진 유저의 비밀번호가 인자로 받은 비밀번호와 일치하는지 판단한다.

        Args:
            - db (Session): db session

        Kwargs:
            - email: 등록 유무를 확인하려는 이메일
            - password: 등록된 이메일을 가진 유저의 패스워드인지 확인하려는 패스워드

        Returns:
            User: 입력된 값들과 일치하는 유저 객체를 반환한다. 없으면 None을 반환
        """
        user = db.query(User).filter(User.email == kwargs.get("email")).first()

        if len(kwargs) == 1:
            return user
        else:
            if not user or not user_service.verify_password(
                kwargs.get("password"), user.password
            ):
                return False
            return user

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
            payload = jwt.decode(token, settings.SECRET_KEY, settings.SECRET_ALGORITHM)
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = db.query(User).filter(User.email == email).first()

        if user is None:
            raise credentials_exception

        return user

    def get_current_user_verified(
        self, current_user: User = Depends(get_current_user)
    ) -> User:
        """인증된 현재 유저 정보를 반환한다.

        Args:
            current_user (Depends): 현재 유저 정보

        Raises:
            HTTPException: 인증되지 않을 경우 발생

        Returns:
            인증된 유저 정보를 반환
        """
        if not current_user.verified:
            raise HTTPException(status_code=400, detail="인증되지 않은 유저입니다.")

        return current_user

    def create(self, db: Session, user_info: schema.UserCreate) -> User:
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
            password=user_service.get_password_hash(user_info.password),
            name=f"user-{name}",
            verified=False,
        )

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
        self, db: Session, user: User, data_to_be_updated: schema.UserUpdate | dict
    ) -> User:
        """user 정보를 수정한다.

        Args:
            db (Session): db session
            user (User): user 정보
            data_to_be_updated (BaseModel | dict): 변경할 유저 정보

        Returns:
            User: 수정된 유저 객체
        """
        obj_data = jsonable_encoder(user)

        if isinstance(data_to_be_updated, dict):
            data_to_be_updated = data_to_be_updated
        else:
            data_to_be_updated = data_to_be_updated.dict(exclude_unset=True)

        for field in obj_data:
            if field in data_to_be_updated:
                setattr(user, field, data_to_be_updated[field])

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def remove(self, db: Session, user_info: User | int) -> dict:
        """전달받은 해당 user를 삭제한다.

        Args:
            db (Session): db session
            user_info (BaseModel | int): user model 정보 또는 user.id 정보

        Returns:
            Dict: 성공 시, 성공 메세지를 반환
        """
        if isinstance(user_info, int):
            user = db.query(User).filter(User.id == user_info).first()
        else:
            user = user_info

        db.delete(user)
        db.commit()

        return {"status": "success"}


class FollowDB:
    def get_follow(self, db: Session, follow_info: schema.Follow):
        db_obj = (
            db.query(Follow)
            .filter(
                Follow.follower_id == follow_info.follower,
                Follow.following_id == follow_info.following,
            )
            .first()
        )

        return db_obj

    def get_followers(self, db: Session, following_id: int):
        # following_id가 따르는 follower들
        return (
            db.query(User)
            .join(User.to_user)
            .filter(Follow.following_id == following_id)
            .all()
        )

    def get_followings(self, db: Session, follower_id: int):
        # follower_id를 따르는 user들
        return (
            db.query(User)
            .join(User.from_user)
            .filter(Follow.follower_id == follower_id)
            .all()
        )

    def follow(self, db: Session, follow_info: schema.Follow):
        db_obj = self.get_follow(db, follow_info)

        if db_obj is None:
            db_obj = Follow(**jsonable_encoder(follow_info))
        else:
            if db_obj.is_followed is False:
                setattr(db_obj, "is_followed", follow_info.is_followed)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def unfollow(self, db: Session, unfollow_info: schema.Unfollow):
        db_obj = self.get_follow(db, unfollow_info)

        if not db_obj:
            raise LookupError("해당 id와 일치하는 객체 정보가 존재하지 않습니다.")
        else:
            if db_obj.is_followed is True:
                setattr(db_obj, "is_followed", unfollow_info.is_followed)

                db.add(db_obj)
                db.commit()
                db.refresh(db_obj)

                return db_obj
            else:
                raise ValueError("is_followed가 이미 False입니다.")


user_crud = UserDB()
follow_crud = FollowDB()
