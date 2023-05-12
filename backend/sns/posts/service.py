from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from sns.posts.schema import PostCreate, PostUpdate
from sns.posts.repository import post_crud
from sns.posts.model import Post


class PostService:
    def get_post(self, db: Session, post_id: int) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 post_id에 해당하는 Post 정보를 조회한다.

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
                status_code=status.HTTP_404_NOT_FOUND, detail="해당 id의 글을 찾을 수 없습니다."
            )
        else:
            return post

    def get_multi_posts(
        self, db: Session, writer_id: int, skip: int = 0, limit: int = 10
    ) -> List[Post]:
        """입력받은 정보를 PostDB class에 전달하여 writer_id 값에 해당되는 user가 작성한 여러 post들을 조회한다.

        Args:
            - writer_id (int): writer user의 id
            - skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            - limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 10

        Raises:
            - HTTPException(404 NOT FOUND): writer_id에 해당되는 writer가 작성한 글이 없을 때 발생하는 에러

        Returns:
            - List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """
        posts = post_crud.get_multi_posts(db, writer_id, skip=skip, limit=limit)

        if len(posts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="작성된 글이 없습니다."
            )
        else:
            return posts

    def create(self, db: Session, post_data: PostCreate, writer_id: int) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 해당 정보를 가지는 post를 생성한다.

        Args:
            post_data (PostCreate): 생성될 post의 content 정보
            writer_id (int): post를 생성하는 user id

        Returns:
            Post: 생성된 post 정보를 반환
        """
        created_post = post_crud.create(db, post_data, writer_id)
        return created_post

    def update(
        self, db: Session, post_data: Post | int, data_to_be_updated: PostUpdate
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여
           post_data에 해당되는 Post 객체에 data_to_be_updated 정보를 반영한다.

        Args:
            post_data (Post | int): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Returns:
            Post: 수정된 post 객체를 반환
        """
        updated_post = post_crud.update(db, post_data, data_to_be_updated)
        return updated_post

    def remove(self, db: Session, post_to_be_deleted: Post | int) -> bool:
        """입력받은 정보를 PostDB class에 전달하여 post_to_be_deleted 해당되는 post 객체를 삭제한다.

        Args:
            post_to_be_deleted (Post | int): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
        """
        post_crud.remove(db, post_to_be_deleted)
        return True


post_service = PostService()
