from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from sns.users.model import User
from sns.comments.repository import comment_crud
from sns.comments.model import Comment


class CommentService:
    def get_comment_and_check_none(
        self,
        db: Session,
        comment_id: int,
    ) -> Comment:
        """입력받은 정보를 CommentDB class에 전달하여 comment_id에 해당하는 Comment 정보를 조회한다.

        Args:
            - comment_id (int): 읽어올 comment의 id

        Raises:
            - HTTPException(404 NOT FOUND): comment_id에 해당되는 comment를 찾을 수 없을 때 발생

        Returns:
            - Comment: comment_id에 해당되는 comment 반환
        """
        comment = comment_crud.get_comment(
            db,
            comment_id,
        )
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 id의 댓글을 찾을 수 없습니다.",
            )
        return comment

    def get_multi_comments_and_check_none(
        self,
        db: Session,
        page: int,
        post_id: int = None,
        writer_id: int = None,
        limit: int = 30,
    ) -> List[Comment]:
        """입력받은 정보를 CommentDB class에 전달하여 post_id 값에 해당되는 여러 comment들을 조회한다.

        Args:
            - post_id (int): post의 id
            - page (int): page number
            - limit (int): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 10

        Raises:
            - HTTPException(404 NOT FOUND): 다음 경우에 발생
                - post_id 또는 writer_id에 해당되는 user가 단 하나의 comment도 작성되지 않았을 때 발생

        Returns:
            - List[Comment]: comment 객체 정보들이 list 배열에 담겨져 반환
        """
        comment_size_per_page = 30

        comments = comment_crud.get_multi_comments(
            db,
            post_id,
            writer_id,
            skip=page * comment_size_per_page,
            limit=limit,
        )

        if len(comments) == 0:
            if post_id and not writer_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="해당 글에 작성된 댓글이 없습니다.",
                )
            elif writer_id and not post_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="해당 유저가 작성한 댓글이 없습니다.",
                )

        else:
            return comments

    def create(
        self,
        db: Session,
        writer_id: int,
        post_id: int,
        data_to_be_created: dict,
    ) -> Comment:
        """입력받은 정보를 CommentDB class에 전달하여 해당 정보를 가지는 comment를 생성한다.

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
        """입력받은 정보를 CommentDB class에 전달하여
           comment_data에 해당되는 Comment 객체를 data_to_be_updated 정보로 수정한다.

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
                detail="글 수정에 실패하였습니다.",
            )

    def remove(
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
            comment_crud.remove(
                db,
                comment_to_be_deleted,
            )
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="댓글 삭제에 실패하였습니다.",
            )

    def create_comment(
        self,
        db: Session,
        writer_id: int,
        current_user: User,
        post_id: int,
        data_to_be_created: dict,
    ) -> Comment:
        """user_id가 current_user와 동일할 때 comment를 생성한다.

        Args:

            - user_id (int): 댓글을 작성할 user의 id
            - current_user (User): 현재 로그인된 user 정보
            - post_id (int): 댓글이 작성될 post의 id
            - data_to_be_created (dict): 생성할 comment의 content 정보

        Raises:

            - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생
            - HTTPException (500 INTERNAL SERVER ERROR): comment 생성에 실패하면 발생

        Returns:

            - Comment: 생성된 comment 정보 반환
        """
        if writer_id == current_user.id:
            new_comment = self.create(
                db,
                writer_id,
                post_id,
                data_to_be_created,
            )
            return new_comment
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="작성할 권한이 없습니다.",
            )

    def update_comment(
        self,
        db: Session,
        user_id: int,
        current_user: User,
        comment_id: int,
        data_to_be_updated: dict,
    ) -> Comment:
        """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 comment_id에 해당되는 comment를 수정한다.

        Args:

            - user_id (int): 수정할 user의 id
            - current_user (User): 현재 유저 정보
            - comment_id (int): 수정될 comment의 id
            - data_to_be_updated (dict): 업데이트할 정보

        Raises:

            - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생
            - HTTPException (404 NOT FOUND): 다음 경우에 대해서 발생한다.
                - comment_id에 해당되는 post를 찾을 수 없을 때 발생
            - HTTPException (500 INTERNAL SERVER ERROR): comment 정보 변경에 실패했을 때 발생

        Returns:

             - Comment: 수정된 comment 객체 반환
        """
        comment = self.get_comment_and_check_none(
            db,
            comment_id,
        )
        if user_id == current_user.id and comment.writer_id == current_user.id:
            self.update(
                db,
                comment,
                data_to_be_updated,
            )
            return comment
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="수정할 권한이 없습니다.",
            )

    def delete_comment(
        self,
        db: Session,
        user_id: int,
        current_user: User,
        comment_id: int,
    ) -> bool:
        """user_id가 current_user의 id와 동일할 때, 해당 comment_id를 가진 comment 삭제한다.

        Args:

            - user_id (int): 삭제시킬 user의 id
            - current_user (User): 현재 로그인된 user 정보
            - comment_id (int): 삭제될 comment의 id

        Raises:

            - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없으면 발생
            - HTTPException (404 NOT FOUND): 다음 경우에 대해서 발생한다.
                - comment_id에 해당되는 comment 찾을 수 없을 때 발생
            - HTTPException (500 INTERNAL SERVER ERROR): comment 삭제에 실패했을 때 발생
        """
        comment = self.get_comment_and_check_none(
            db,
            comment_id,
        )
        if user_id == current_user.id and comment.writer_id == current_user.id:
            self.remove(
                db,
                comment,
            )
            return True
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="삭제할 권한이 없습니다.",
            )


comment_service = CommentService()
