from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.users.model import User
from sns.posts.model import Post, PostLike
from sns.posts import schema
from sns.posts.schema import PostCreate, PostUpdate


class PostDB:
    def get_post(self, db: Session, post_id: int) -> Post:
        """post_id에 해당되는 post 정보를 조회한다.

        Args:
            db (Session): db session
            post_id (int): 조회할 post의 id 값

        Returns:
            Post: post_id에 해당되는 Post 객체 정보. 조회 결과 없으면 None을 반환
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        return post

    def get_multi_posts(
        self, db: Session, writer_id: int, skip: int = 0, limit: int = 10
    ) -> List[Post]:
        """writer_id 값에 해당되는 user가 작성한 여러 post들을 조회하여 생성날짜를 기준으로 최신순으로 정렬하여 반환한다.

        Args:
            db (Session): db session
            writer_id (int): writer user의 id
            skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 100

        Returns:
            List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """

        query = (
            db.query(Post)
            .filter(Post.writer_id == writer_id)
            .order_by(Post.created_at.desc())
        )
        if skip != 0 or limit != 0:
            query = query.offset(skip).limit(limit)

        return query.all()

    def create(self, db: Session, post_data: PostCreate, writer_id: int) -> Post:
        """주어진 post_data, writer_id 정보를 가지는 post를 생성한다.

        Args:
            db (Session): db session
            post_data (PostCreate): 생성될 post의 content 정보
            writer_id (int): post를 생성하는 user id

        Returns:
            Post: 생성된 post 정보를 반환
        """
        new_post = Post(content=post_data.content, writer_id=writer_id)

        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return new_post

    def update(
        self, db: Session, post_data: Post, data_to_be_updated: PostUpdate
    ) -> Post:
        """post_info에 해당되는 Post 객체를 data_to_be_updated 정보를 가지도록 수정한다.

        Args:
            db (Session): db session
            post_data (Post): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Returns:
            Post: 수정된 post 객체를 반환
        """
        if isinstance(data_to_be_updated, dict):
            data_to_be_updated = data_to_be_updated
        else:
            data_to_be_updated = data_to_be_updated.dict(exclude_unset=True)

        for field in jsonable_encoder(post_data):
            if field in data_to_be_updated:
                setattr(post_data, field, data_to_be_updated[field])

        db.add(post_data)
        db.commit()
        db.refresh(post_data)

        return post_data

    def remove(self, db: Session, post_to_be_deleted: Post) -> bool:
        """post_to_be_deleted 해당되는 post 객체를 삭제한다.

        Args:
            db (Session): db session
            post_to_be_deleted (Post): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
        """
        db.delete(post_to_be_deleted)
        db.commit()


class PostLikeDB:
    def get_like(self, db: Session, post_like_data: schema.PostLikeBase) -> PostLike:
        return (
            db.query(PostLike)
            .filter(
                PostLike.like_target_id == post_like_data.like_target_id,
                PostLike.who_like_id == post_like_data.who_like_id,
            )
            .first()
        )

    def get_users_who_like(self, db: Session, like_target_id: int) -> List[User]:
        """like_target_id에 일치하는 post를 좋아요한 liker 유저들을 조회한다.

        Args:
            db (Session): db session
            like_target_id (int): like를 받은 post의 id

        Returns:
            List[User]: list 데이터 타입에 담겨진 User 객체
        """
        # like_target_id에 해당되는 post에 좋아요를 누른 다수의 user 조회
        return (
            db.query(User)
            .join(User.liker)
            .filter(PostLike.like_target_id == like_target_id, PostLike.is_liked)
            .order_by(PostLike.updated_at.desc())
            .all()
        )

    def get_like_targets(self, db: Session, who_like_id: int) -> List[Post]:
        """who_like_id에 해당하는 user가 좋아요를 표시한 likee인 다수의 post를 조회한다.

        Args:
            db (Session): db session
            who_like_id (int): 작성된 post에 좋아요를 한 user의 id

        Returns:
            List[Post]: list 데이터 타입에 담겨진 Post 객체 정보들
        """
        return (
            db.query(Post)
            .join(Post.likee)
            .filter(PostLike.who_like_id == who_like_id, PostLike.is_liked)
            .order_by(PostLike.updated_at.desc())
            .all()
        )

    def like(self, db: Session, like_data: schema.PostLike) -> PostLike:
        """like_data 를 토대로 post에 좋아요를 실행한다.

        Args:
            db (Session): db session
            like_data (schema.PostLike): who_like_id, like_target_id, is_liked 값 정보

        Returns:
            PostLike: is_liked 값이 True로 생성된 PostLike 객체를 반환
        """
        selected_post_like = self.get_like(db, like_data)

        if selected_post_like and not selected_post_like.is_liked:
            setattr(selected_post_like, "is_liked", like_data.is_liked)
            new_like = selected_post_like
        else:
            new_like = PostLike(**like_data.dict())

        db.add(new_like)
        db.commit()
        db.refresh(new_like)

        return new_like

    def unlike(self, db: Session, unlike_data: schema.PostUnlike) -> PostLike:
        """like_data 를 토대로 post에 좋아요를 취소한다.

        Args:
            db (Session): db session
            unlike_data (schema.PostLike): who_like_id, like_target_id, is_liked 값 정보

        Raises:
            ValueError: is_liked 값이 이미 False인 경우 발생되는 에러

        Returns:
            PostLike: is_liked 값이 변경된 PostLike 객체를 반환
        """
        selected_like = self.get_like(db, unlike_data)
        setattr(selected_like, "is_liked", unlike_data.is_liked)

        db.add(selected_like)
        db.commit()
        db.refresh(selected_like)

        return selected_like


post_crud = PostDB()
post_like_crud = PostLikeDB()
