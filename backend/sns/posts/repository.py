from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.posts.model import Post
from sns.posts.schema import PostCreate, PostUpdate


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

    def create(self, db: Session, post_data: PostCreate, writer_id: int) -> Post:
        """주어진 post_data, writer_id 정보를 가지는 post를 생성한다.

        Args:
            post_data (PostCreate): 생성될 post의 content 정보
            writer_id (int): post를 생성하는 user id

        Returns:
            Post: 생성된 post 정보를 반환
        """
        db_obj = Post(content=post_data.content, writer_id=writer_id)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
        self, db: Session, post_data: Post | int, data_to_be_updated: PostUpdate
    ) -> Post:
        """post_info에 해당되는 Post 객체를 data_to_be_updated 정보를 가지도록 수정한다.

        Args:
            post_data (Post | int): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Returns:
            Post: 수정된 post 객체를 반환
        """
        if isinstance(post_data, int):
            post = db.query(Post).filter(Post.id == post_data).first()
        else:
            post = post_data

        if isinstance(data_to_be_updated, dict):
            data_to_be_updated = data_to_be_updated
        else:
            data_to_be_updated = data_to_be_updated.dict(exclude_unset=True)

        for field in jsonable_encoder(post):  # post.dict()
            if field in data_to_be_updated:
                setattr(post, field, data_to_be_updated[field])

        db.add(post)
        db.commit()
        db.refresh(post)

        return post

    def remove(self, db: Session, post_to_be_deleted: Post | int) -> bool:
        """post_to_be_deleted 해당되는 post 객체를 삭제한다.

        Args:
            post_to_be_deleted (Post | int): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
        """
        if isinstance(post_to_be_deleted, int):
            post = db.query(Post).filter(Post.id == post_to_be_deleted).first()
        else:
            post = post_to_be_deleted
        db.delete(post)
        db.commit()


post_crud = PostDB()
