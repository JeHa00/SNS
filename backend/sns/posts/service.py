from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from sns.users.model import User
from sns.posts.schema import PostCreate, PostUpdate
from sns.posts.repository import post_crud
from sns.posts.model import Post


class PostService:
    def get_post_and_check_none(
        self,
        db: Session,
        post_id: int,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 post_id에 해당하는 Post 정보를 조회한다.

        Args:
            - post_id (int): 읽어올 post의 id

        Raises:
            - HTTPException(404 NOT FOUND): post_id에 해당되는 post를 찾을 수 없을 때 발생

        Returns:
            - Post: post_id에 해당되는 post 반환
        """
        post = post_crud.get_post(
            db,
            post_id,
        )
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 id의 글을 찾을 수 없습니다.",
            )
        return post

    def get_multi_posts(
        self,
        db: Session,
        writer_id: int,
        skip: int = 0,
        limit: int = 10,
    ) -> List[Post]:
        """입력받은 정보를 PostDB class에 전달하여 writer_id 값에 해당되는 user가 작성한 여러 post들을 조회한다.

        Args:
            - writer_id (int): writer user의 id
            - skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            - limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 10

        Raises:
            - HTTPException(404 NOT FOUND): 다음 경우에 발생
                - writer_id에 해당되는 user가 단 하나의 post도 작성하지 않았을 때 발생

        Returns:
            - List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """
        posts = post_crud.get_multi_posts(
            db,
            writer_id,
            skip=skip,
            limit=limit,
        )

        if len(posts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작성된 글이 없습니다.",
            )
        else:
            return posts

    def create(
        self,
        db: Session,
        post_data: PostCreate,
        writer_id: int,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 해당 정보를 가지는 post를 생성한다.

        Args:
            - post_data (PostCreate): 생성될 post의 content 정보
            - writer_id (int): post를 생성하는 user id

        Raises:
            - HTTPException(500 INTERNAL SERVER ERROR): post 생성에 실패했을 때 발생

        Returns:
            - Post: 생성된 post 정보를 반환
        """
        try:
            created_post = post_crud.create(
                db,
                post_data,
                writer_id,
            )
            return created_post
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 생성에 실패하였습니다.",
            )

    def update(
        self,
        db: Session,
        post_data: Post,
        data_to_be_updated: PostUpdate,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여
           post_data에 해당되는 Post 객체에 data_to_be_updated 정보로 수정한다.

        Args:
            - post_data (Post): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            - data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Raises:
            - HTTPException(500 INTERNAL SERVER ERROR): post 수정 실패 시 발생

        Returns:
            - Post: 수정된 post 객체를 반환
        """
        try:
            updated_post = post_crud.update(
                db,
                post_data,
                data_to_be_updated,
            )
            return updated_post
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 수정에 실패하였습니다.",
            )

    def remove(
        self,
        db: Session,
        post_to_be_deleted: Post,
    ) -> bool:
        """입력받은 정보를 PostDB class에 전달하여 post_to_be_deleted 해당되는 post 객체를 삭제한다.

        Args:
            - post_to_be_deleted (Post): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.

        Raises:
            - HTTPException(500 INTERNAL SERVER ERROR): post 삭제에 실패했을 때 발생

        Returns:
            - bool: post 삭제에 성공하면 True를 반환
        """
        try:
            post_crud.remove(
                db,
                post_to_be_deleted,
            )
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 삭제에 실패하였습니다.",
            )

    def create_post(
        self,
        db: Session,
        user_id: int,
        data_to_be_created: PostCreate,
        current_user: User,
    ) -> Post:
        """user_id가 current_user와 동일할 때 post를 생성한다.

        Args:

            - user_id (int): 글을 작성할 user의 id
            - data_to_be_created (PostCreate): 생성할 post의 content 정보
            - current_user (User, optional): 현재 로그인된 user 정보

        Raises:

            - HTTPException(500 INTERNAL SERVER ERROR): post 생성에 실패하면 발생
            - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생

        Returns:

              - Post: 생성된 post 정보 반환
        """
        if user_id == current_user.id:
            post = self.create(db, data_to_be_created, user_id)
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="작성할 권한이 없습니다.",
            )

    def update_post(
        self,
        db: Session,
        user_id: int,
        post_id: int,
        data_to_be_updated: PostUpdate,
        current_user: User,
    ) -> Post:
        """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 post를 수정한다.

        Args:

            - user_id (int): 수정할 user의 id
            - post_id (int): 수정될 post의 id
            - data_to_be_updated (PostUpdate): 업데이트할 정보
            - current_user (User): 현재 유저 정보

        Raises:

            - HTTPException(404 NOT FOUND): 다음 경우에 대해서 발생한다.
                - post_id에 해당되는 post를 찾을 수 없을 때 발생
            - HTTPException(500 INTERNAL SERVER ERROR): post 정보 변경에 실패했을 때 발생
            - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생

        Returns:

             - Post: 수정된 post 객체 반환
        """
        post = self.get_post_and_check_none(
            db,
            post_id,
        )
        if user_id == current_user.id and post.writer_id == current_user.id:
            self.update(
                db,
                post,
                data_to_be_updated,
            )
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="수정할 권한이 없습니다.",
            )

    def delete_post(
        self,
        db: Session,
        user_id: int,
        post_id: int,
        current_user: User,
    ) -> None:
        """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

        Args:

            - user_id (int): 삭제시킬 user의 id
            - post_id (int): 삭제될 post의 id
            - current_user (User): 현재 로그인된 user 정보

        Raises:

            - HTTPException(404 NOT FOUND): 다음 경우에 대해서 발생한다.
                - post_id에 해당되는 post를 찾을 수 없을 때 발생
            - HTTPException(500 INTERNAL SERVER ERROR): post 삭제에 실패했을 때 발생
            - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생
        """
        post = self.get_post_and_check_none(
            db,
            post_id=post_id,
        )
        if user_id == current_user.id and post.writer_id == current_user.id:
            self.remove(
                db,
                post_to_be_deleted=post,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="삭제할 권한이 없습니다.",
            )


post_service = PostService()
