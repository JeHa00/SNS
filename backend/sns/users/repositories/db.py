import secrets

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.users.model import User
from sns.users import schema


class UserDB:
    def get_user(
        self,
        db: Session,
        email: str = None,
        user_id: int = None,
        verification_code: str = None,
    ) -> User:
        """이메일이 이미 등록되어있는지 또는 해당 이메일을 가진 유저의 비밀번호가 인자로 받은 비밀번호와 일치하는지 판단한다.

        Args:
            - db (Session): db session

        Kwargs:
            - email: 등록 유무를 확인하려는 이메일
            - password: 등록된 이메일을 가진 유저의 패스워드인지 확인하려는 패스워드

        Returns:
            User: 입력된 값들과 일치하는 유저 객체를 반환한다. 없으면 None을 반환
        """
        if email is not None:
            user = db.query(User).filter(email == email).first()
        elif user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()
        else:
            user = db.query(User).filter(verification_code == verification_code).first()

        return user

    def create(self, db: Session, data_for_signup: schema.UserCreate) -> User:
        """받은 정보로 새 유저를 등록한다.

        Args:
            db (Session): db session
            data_for_signup (UserCreate): 새로 등록한 유저의 email과 password

        Returns:
            User: 새로 생성한 유저 객체
        """
        name = secrets.token_urlsafe(8)  # minimum name length

        db_obj = User(
            email=data_for_signup.email,
            password=data_for_signup.password,
            name=f"user-{name}",
            verified=data_for_signup.verified,
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
            User: 수정된 user 객체
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

    def remove(self, db: Session, user_to_be_deleted: User | int) -> dict:
        """전달받은 해당 user를 삭제한다.

        Args:
            db (Session): db session
            user_to_be_deleted (BaseModel | int): user model 정보 또는 user.id 정보

        Returns:
            Dict: 성공 시, 성공 메세지를 반환
        """
        if isinstance(user_to_be_deleted, int):
            user = self.get_user(db, user_id=user_to_be_deleted)
        else:
            user = user_to_be_deleted

        db.delete(user)
        db.commit()

        return {"status": "success"}


user_crud = UserDB()
