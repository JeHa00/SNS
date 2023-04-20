from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.users.model import User
from sns.posts.model import Post, PostLike
from sns.posts import schema


class PostDB:
    def get_post(self, db: Session, post_id: int) -> Post:
        """post_id에 해당되는 post 정보를 조회한다.

        Args:
            post_id (int): 조회할 post의 id 값

        Returns:
            Post: post_id에 해당되는 Post 객체 정보. 조회 결과 없으면 None을 반환
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        return post

    def get_multi_posts(
        self, db: Session, writer_id: int, skip: int = 0, limit: int = 100
    ) -> List[Post]:
        """writer_id 값에 해당되는 user가 작성한 여러 post들을 조회한다.

        Args:
            writer_id (int): writer user의 id
            skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 100

        Returns:
            List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """
        return (
            db.query(Post)
            .filter(writer_id == writer_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, post_info: schema.PostCreate, writer_id: int) -> Post:
        """주어진 post_info, writer_id 정보를 가지는 post를 생성한다.

        Args:
            post_info (PostCreate): 생성될 post의 content 정보
            writer_id (int): post를 생성하는 user id

        Returns:
            Post: 생성된 post 정보를 반환
        """
        obj_in_data = jsonable_encoder(post_info)
        content = obj_in_data.get("content")
        db_obj = Post(content=content, writer_id=writer_id)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
        self, db: Session, post_info: Post | int, data_to_be_updated: schema.PostUpdate
    ) -> Post:
        """post_info에 해당되는 Post 객체를 data_to_be_updated 정보를 가지도록 수정한다.

        Args:
            post_info (Post | int): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Returns:
            Post: 수정된 post 객체를 반환
        """
        if isinstance(post_info, int):
            post = db.query(Post).filter(Post.id == post_info).first()
        else:
            post = post_info

        obj_data = jsonable_encoder(post)

        if isinstance(data_to_be_updated, dict):
            data_to_be_updated = data_to_be_updated
        else:
            data_to_be_updated = data_to_be_updated.dict(exclude_unset=True)

        for field in obj_data:
            if field in data_to_be_updated:
                setattr(post, field, data_to_be_updated[field])

        db.add(post)
        db.commit()
        db.refresh(post)

        return post

    def remove(self, db: Session, post_info: Post | int) -> bool:
        """post_info 해당되는 post 객체를 삭제한다.

        Args:
            post_info (Post | int): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
        """
        if isinstance(post_info, int):
            post = db.query(Post).filter(Post.id == post_info).first()
        else:
            post = post_info
        db.delete(post)
        db.commit()


class PostLikeDB:
    # liker 조회
    def get_users_who_like(self, db: Session, like_target_id: int) -> List[User]:
        """like_target_id에 일치하는 post를 좋아요한 유저들을 조회한다.

        Args:
            like_target_id (int): like를 받은 post의 id

        Returns:
            _type_: _description_
        """
        # like_target_id에 해당되는 post에 좋아요를 누른 다수의 user 조회
        return (
            db.query(PostLike)
            .filter(PostLike.like_target_id == like_target_id, PostLike.is_like is True)
            .all()
        )

    # likee 조회
    def get_like_targets(self, db: Session, who_like_id: int):
        # who_like_id에 해당되는 user가 좋아요를 누른 다수의 post 조회
        # return db.query(PostLike).filter(PostLike.who_like_id == who_like_id).all()
        return (
            db.query(PostLike)
            .filter(PostLike.who_like_id == who_like_id, PostLike.is_like is True)
            .all()
        )

    def like(self, db: Session, like_info: schema.PostLike):
        is_like, who_like_id, like_target_id = like_info.values()

        db_obj = (
            db.query(PostLike)
            .filter(
                PostLike.who_like_id == who_like_id,
                PostLike.like_target_id == like_target_id,
            )
            .first()
        )

        if db_obj is None:
            db_obj = PostLike(**like_info)
        else:
            setattr(db_obj, "is_like", is_like)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def unlike(self, db: Session, unlike_info: schema.PostUnlike):
        is_like, who_like_id, like_target_id = unlike_info.values()

        db_obj = (
            db.query(PostLike)
            .filter(
                PostLike.who_like_id == who_like_id,
                PostLike.like_target_id == like_target_id,
            )
            .first()
        )

        setattr(db_obj, "is_like", is_like)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj


post_crud = PostDB()
post_like_crud = PostLikeDB()
