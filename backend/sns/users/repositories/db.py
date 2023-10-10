from typing import List

from sqlalchemy.orm import Session

from sns.users.model import User, Follow


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
        if email:
            user = db.query(User).filter(User.email == email).one_or_none()
        elif user_id:
            user = db.query(User).filter(User.id == user_id).one_or_none()
        else:
            user = (
                db.query(User)
                .filter(User.verification_code == verification_code)
                .one_or_none()
            )

        return user

    def create(self, db: Session, **kwargs: dict) -> User:
        """받은 정보로 새 유저를 등록한다.

        Args:
            db (Session): db session
            kwargs (dict): 새로 등록한 유저의 email과 password

        Returns:
            User: 새로 생성한 유저 객체
        """
        new_user = User(**kwargs)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    def update(
        self,
        db: Session,
        user: User,
        **kwargs,
    ) -> User:
        """user 정보를 수정한다.

        Args:
            db (Session): db session
            user (User): user 정보
            data_to_be_updated (BaseModel | dict): 변경할 유저 정보

        Returns:
            User: 수정된 user 객체
        """
        data_to_be_updated = {
            key: value
            for key, value in kwargs.items()
            if hasattr(user, key) and value is not None
        }

        for key, value in data_to_be_updated.items():
            setattr(user, key, value)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def remove(
        self,
        db: Session,
        user_to_be_deleted: User | int,
    ) -> dict:
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

    def get_follow(
        self,
        db: Session,
        follower_id: int,
        following_id: int,
    ) -> Follow:
        """follow_data에 일치하는 Follow 객체를 조회한다.

        Args:
            db (Session): db session
            follower_id (int): follower의 id
            following_id (int): following의 id

        Returns:
            Follow: 일치한 Follow 객체를 반환
        """
        selected_follow = (
            db.query(Follow)
            .filter(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
            .one_or_none()
        )

        return selected_follow

    def get_a_follow_by_id(
        self,
        db: Session,
        follow_id: int,
    ) -> Follow:
        """follow_id에 해당하는 Follow 객체를 조회한다.

        Args:
            db (Session): db session
            follow_id (int): follow의 id

        Returns:
            Follow: 조회된 Follow 객체
        """
        return db.query(Follow).filter(Follow.id == follow_id).one_or_none()

    def get_followers(
        self,
        db: Session,
        following_id: int,
    ) -> List[User]:
        """following_id에 해당하는 user가 따르는 follower들을 조회한다.

        Args:
            db (Session): db session
            following_id (int): follow 신청을 한 user id

        Returns:
            List[User]: following_id로부터 follow 신청을 받은 user 목록
        """
        subquery = (
            db.query(Follow).filter(Follow.following_id == following_id).subquery()
        )

        return db.query(User).join(subquery, User.id == subquery.c.follower_id).all()

    def get_followings(
        self,
        db: Session,
        follower_id: int,
    ) -> List[User]:
        """follow_id에 해당하는 user를 따르는 following들을 조회한다.

        Args:
            db (Session): db session
            follower_id (int): follow 신청을 받은 user id

        Returns:
            List[User]: follower_id를 따르는 user 목록
        """
        subquery = db.query(Follow).filter(Follow.follower_id == follower_id).subquery()

        return db.query(User).join(subquery, User.id == subquery.c.following_id).all()

    def follow(
        self,
        db: Session,
        selected_follow_data: None | Follow,
        follower_id: int,
        following_id: int,
    ) -> Follow:
        """follow_data 를 토대로 follow 관계를 맺기 위해 Follow 객체를 생성한다.

        Args:
            db (Session): db session
            follow_data (dict): follower와 following의 id 정보

        Returns:
            Follow: 생성된 Follow 객체를 반환
        """
        new_follow = selected_follow_data or Follow(
            is_followed=True,
            follower_id=follower_id,
            following_id=following_id,
        )
        if not new_follow.is_followed:
            new_follow.is_followed = True

        db.add(new_follow)
        db.commit()
        db.refresh(new_follow)

        return new_follow

    def unfollow(
        self,
        db: Session,
        selected_follow_data: Follow,
    ) -> Follow:
        """selected_follow_data 토대로 follow 관계를 취소하기 위해 is_followed 값을 False로 변경한다.

        Args:
            db (Session): db session
            selected_follow_data (dict): follower와 following의 id 정보

        Returns:
            Follow: follow 관계가 끊어진 Follow 객체 정보를 반환
        """
        selected_follow_data.is_followed = False

        db.add(selected_follow_data)
        db.commit()
        db.refresh(selected_follow_data)

        return selected_follow_data


user_crud = UserDB()
