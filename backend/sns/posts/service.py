from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from sns.posts.model import Post
from sns.posts.repository import post_crud
from sns.posts.schema import PostCreate, PostUpdate


class PostService:
    def get_post(self, db: Session, post_id: int) -> Post:
        """post_id와 일치하는 post.id를 가진 post 정보를 읽어온다.

        Args:
            - post_id (int): 읽어올 post의 id

        Raises:
            - HTTPException(404 NOT FOUND): post_id에 해당되는 post를 찾을 수 없을 때 발생하는 에러

        Returns:
            - Post: post_id에 해당되는 post 반환
        """
        post = post_crud.get_post(db, post_id)

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="해당 id의 포스트를 찾을 수 없습니다."
            )
        else:
            return post

    def get_multi_posts(self, db: Session, writer_id: int) -> List[Post]:
        posts = post_crud.get_multi_posts(db, writer_id)

        if len(posts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="작성된 글이 없습니다."
            )

        else:
            return posts

    def create(self, db: Session, post_data: PostCreate, writer_id: int) -> Post:
        created_post = post_crud.create(db, post_data, writer_id)
        return created_post

    def update(
        self, db: Session, post_data: Post | int, data_to_be_updated: PostUpdate
    ) -> Post:
        updated_post = post_crud.update(db, post_data, data_to_be_updated)
        return updated_post

    def remove(self, db: Session, post_to_be_deleted: Post | int) -> bool:
        post_crud.remove(db, post_to_be_deleted)
        return {"status": "success"}


post_service = PostService()
