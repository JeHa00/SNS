from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from sns.common.http_exceptions import CommonHTTPExceptions
from sns.users.model import User
from sns.users.repositories.db import user_crud
from sns.posts.model import Post
from sns.posts.repository import post_crud
from sns.comments.model import Comment
from sns.comments.repository import comment_crud


class CommentService:
    COMMENT_COUNT_PER_PAGE = 30

    def get_a_comment_and_handle_none(
        self,
        db: Session,
        comment_id: int,
    ) -> Comment:
        """주어진 정보에 해당되는 댓글을 조회하고, 없을 경우 404 에러를 발생시킨다.

        Args:
            db (Session): db session
            comment_id (int): 조회할 댓글의 id

        Raises:
            HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우
                - code: COMMENT_NOT_FOUND

        Returns:
            Comment: 주어진 정보에 해당되는 댓글 정보를 반환
        """
        comment = comment_crud.get_a_comment(
            db,
            comment_id,
        )

        if not comment:
            raise CommonHTTPExceptions.COMMENT_NOT_FOUND_ERROR

        return comment

    def get_a_user_and_handle_none(
        self,
        db: Session,
        user_id: int,
    ) -> User:
        """주어진 정보에 해당되는 유저를 조회하고, 없을 경우 404 에러를 발생시킨다.

        Args:
            db (Session): db session
            user_id (int): 조회할 유저의 id

        Raises:
            HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 유저가 없을 경우
                - code: USER_NOT_FOUND

        Returns:
            User: 주어진 정보에 해당되는 유저 정보를 반환
        """
        user = user_crud.get_user(
            db,
            user_id=user_id,
        )

        if not user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        return user

    def get_a_post_and_handle_none(
        self,
        db: Session,
        post_id: int,
    ) -> Post:
        """주어진 정보에 해당되는 글을 조회하고, 없을 경우 404 에러를 발생시킵니다.

        Args:
            db (Session): db session
            post_id (int): 조회할 글의 id

        Raises:
            HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 글이 없을 경우
                - code: POST_NOT_FOUND

        Returns:
            Post: 주어진 정보에 해당되는 글 정보를 반환
        """
        post = post_crud.get_post(
            db,
            post_id,
        )

        if not post:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return post

    def create(
        self,
        db: Session,
        writer_id: int,
        post_id: int,
        data_to_be_created: dict,
    ) -> Comment:
        """주어진 정보를 토대로 comment를 생성한다.

        Args:
            - writer_id (int): comment를 생성하는 user id
            - post_id (int): comment가 달리는 post id
            - data_to_be_created (dict): 생성될 comment의 content 정보

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): comment 생성에 실패했을 때 발생

        Returns:
            - Comment: 생성된 comment 정보를 반환
        """
        try:
            created_comment = comment_crud.create(
                db,
                writer_id,
                post_id,
                **data_to_be_created,
            )
            return created_comment
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="댓글 생성에 실패하였습니다.",
            )

    def update(
        self,
        db: Session,
        comment: Comment,
        data_to_be_updated: dict,
    ) -> Comment:
        """comment_data에 해당되는 Comment 객체를 data_to_be_updated 정보로 수정한다.

        Args:
            - comment (Comment): 수정할 Comment 객체 정보
            - data_to_be_updated (dict): 수정 시 반영할 내용

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): comment 수정 실패 시 발생

        Returns:
            - Comment: 수정된 comment 객체를 반환
        """
        try:
            updated_comment = comment_crud.update(
                db,
                comment,
                **data_to_be_updated,
            )
            return updated_comment
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="댓글 수정에 실패하였습니다.",
            )

    def delete(
        self,
        db: Session,
        comment_to_be_deleted: Comment,
    ) -> bool:
        """입력받은 정보를 CommentDB class에 전달하여 comment_to_be_deleted 해당되는 comment 객체를 삭제한다.

        Args:
            - comment_to_be_deleted (Comment): 삭제할 Comment 객체 정보

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): comment 삭제에 실패했을 때 발생

        Returns:
            - bool: comment 삭제에 성공하면 True를 반환
        """
        try:
            comment_crud.delete(
                db,
                comment_to_be_deleted,
            )
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="댓글 삭제에 실패하였습니다.",
            )

    def get_comments_on_a_post(
        self,
        db: Session,
        post_id: int,
        page: int,
    ) -> List[Comment]:
        """post_id에 해당하는 글에 작성된 댓글들을 조회한다.
        한 번 조회시 최대 30개를 조회한다. 다음 30개 댓글을 조회하고 싶다면 page 매개변수를 통해 조절한다.

        Args:
            - db (Session): db session
            - post_id (int): 작성된 글의 id
            - page (int): 조회 시 offset 하기 위한 page

        Raises:
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 글이 없을 경우
                - code: POST_NOT_FOUND
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우
                - code: COMMENT_NOT_FOUND

        turns:
            - List[Comment]: 여러 댓글 정보들이 리스트에 담겨진 형태로 반환
        """
        # 글 유무 확인
        self.get_a_post_and_handle_none(db, post_id)

        # 댓글 정보 조회
        comments = comment_crud.get_comments_by_post_id(
            db,
            post_id,
            skip=page * self.COMMENT_COUNT_PER_PAGE,
        )

        if not comments:
            raise CommonHTTPExceptions.COMMENT_NOT_FOUND_ERROR

        return comments

    def get_comments_of_a_user(
        self,
        db: Session,
        user_id: int,
        page: int,
    ) -> List[Comment]:
        """user_id에 해당되는 유저가 작성한 댓글들을 조회한다.
        한 번 조회시 최대 30개를 조회한다. 다음 30개를 조회하고 싶다면 page 매개변수를 통해 조절한다.

        Args:
            - db (Session): db session
            - user_id (int): 유저의 id
            - page (int): 조회 시 offset 하기 위한 page

        Raises:
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 유저가 없을 경우
                - code: USER_NOT_FOUND
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우
                - code: COMMENT_NOT_FOUND

        Returns:
            - List[Comment]: 여러 댓글 정보들이 리스트에 담겨진 형태로 반환
        """
        # 유저 유무 확인
        self.get_a_user_and_handle_none(db, user_id)

        comments = comment_crud.get_comments_by_writer_id(
            db,
            user_id,
            skip=page * self.COMMENT_COUNT_PER_PAGE,
        )

        if not comments:
            raise CommonHTTPExceptions.COMMENT_NOT_FOUND_ERROR

        return comments

    def create_comment(
        self,
        db: Session,
        writer_id: int,
        current_user_id: int,
        post_id: int,
        content: str,
    ) -> Comment:
        """writer_id가 current_user_id와 동일할 때 comment를 생성한다.

        Args:
            - db (Session): db session
            - writer_id (int): 댓글을 작성할 user의 id
            - current_user_id (int): 현재 로그인된 유저의 id
            - post_id (int): 댓글이 작성될 post의 id
            - content (str): 생성할 댓글의 content 정보

        Raises:
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 유저가 없을 경우
                - code: USER_NOT_FOUND
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 글이 없을 경우
                - code: POST_NOT_FOUND
            - HTTPException (403 FORBIDDEN): writer_id와 current_user_id가 다르면 발생
            - HTTPException (500 INTERNAL SERVER ERROR): 댓글 생성에 실패하면 발생

        Returns:

            - Comment: 생성된 comment 정보 반환
        """
        # 유저 유무 확인
        self.get_a_user_and_handle_none(db, writer_id)

        # 글 유무 확인
        self.get_a_post_and_handle_none(db, post_id)

        if writer_id == current_user_id:
            new_comment = self.create(
                db,
                writer_id,
                post_id,
                content,
            )
            return new_comment
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="작성 권한이 없습니다.",
            )

    def update_comment(
        self,
        db: Session,
        current_user_id: int,
        comment_id: int,
        data_to_be_updated: dict,
    ) -> Comment:
        """수정하려는 댓글의 작성자가 current_user_id와 동일하여 수정 권한이 있을 때 댓글을 수정한다.

        Args:
            - db (Session): db session
            - current_user_id (int): 현재 로그인된 유저의 id
            - comment_id (int): 수정 대상 댓글의 id
            - data_to_be_updated (dict): 업데이트할 정보

        Raises:
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우
                - code: COMMENT_NOT_FOUND
            - HTTPException (403 FORBIDDEN): 댓글의 작성자가 로그인한 유저의 id와 달라 작성 권한이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): 댓글 정보 변경에 실패했을 때 발생

        Returns:

            - Comment: 수정된 comment 객체 반환
        """
        # 댓글 유무 확인
        selected_comment = self.get_a_comment_and_handle_none(db, comment_id)

        if selected_comment.writer_id == current_user_id:
            self.update(
                db,
                selected_comment,
                data_to_be_updated,
            )
            return selected_comment
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="수정 권한이 없습니다.",
            )

    def delete_comment(
        self,
        db: Session,
        current_user_id: int,
        comment_id: int,
    ) -> bool:
        """삭제하려는 댓글의 작성자가 current_user_id와 동일할 때, 해당 댓글을 삭제한다.

        Args:
            - db (Session): db session
            - current_user_id (int): 현재 로그인된 유저의 id
            - comment_id (int): 삭제될 comment의 id

        Raises:
            - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우
                - code: COMMENT_NOT_FOUND)
            - HTTPException (403 FORBIDDEN): 댓글의 작성자가 로그인한 유저의 id와 달라 삭제 권한이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): 댓글 삭제에 실패했을 때 발생

        Returns:

            - bool: 삭제 완료 시 True 반환
        """
        # 댓글 유무 확인
        selected_comment = self.get_a_comment_and_handle_none(db, comment_id)

        if selected_comment.writer_id == current_user_id:
            self.delete(
                db,
                selected_comment,
            )
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="삭제 권한이 없습니다.",
            )


comment_service = CommentService()
