from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import UserService
from sns.users.model import User
from sns.users.schema import Msg
from sns.posts.service import PostService
from sns.comments.service import CommentService
from sns.comments import schema

router = APIRouter()


@router.get(
    "/posts/{post_id}/comments",
    response_model=List[schema.Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_on_a_post(
    post_id: int,
    page: int,
    post_service: PostService = Depends(PostService),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> List[schema.Comment]:
    """한 개의 post에 대한 모든 comment를 조회한다.

    Args:
        - post_id (int): comment가 달린 post의 id
        - page (int): page 번호

    Raises:
        - HTTPException (404 NOT FOUND): 다음 2가지 경우에 발생한다.
            - post_id에 해당되는 post가 존재하지 않는 경우
            - post_id에 달린 댓글이 0개일 경우

    Returns:
        - List[schema.Comment]: 해당되는 여러 comment를 list에 담겨 반환
    """
    post_service.get_post_and_check_none(
        db,
        post_id=post_id,
    )
    comments = comment_service.get_multi_comments_and_check_none(
        db,
        page,
        post_id=post_id,
    )
    return comments


@router.get(
    "/users/{user_id}/comments",
    response_model=List[schema.Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_of_a_user(
    user_id: int,
    page: int,
    user_service: UserService = Depends(UserService),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> List[schema.Comment]:
    """한 user가 작성한 모든 comment를 조회한다.

    Args:
        - user_id (int): comment를 작성한 user의 id
        - page (int): page 번호

    Raises:
        - HTTPException (404 NOT FOUND): 다음 2가지 경우일 때 발생된다.
            - user_id에 해당되는 user가 작성한 댓글이 없을 경우
            - user_id로 등록된 회원이 없을 경우

    Returns:
        - List[schema.Comment]: 해당되는 여러 comment를 list에 담겨 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(selected_user)
    comments = comment_service.get_multi_comments_and_check_none(
        db,
        page,
        writer_id=user_id,
    )
    return comments


@router.post(
    "/users/{writer_id}/posts/{post_id}/comments",
    response_model=schema.Comment,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    writer_id: int,
    post_id: int,
    data_to_be_created: schema.CommentCreate,
    current_user: User = Depends(UserService.get_current_user_verified),
    user_service: UserService = Depends(UserService),
    post_service: PostService = Depends(PostService),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> schema.Comment:
    """전달된 정보로 comment를 생성한다.

    Args:
        - writer_id (int): comment를 생성할 user의 id
        - post_id (int): comment가 작성될 post의 id
        - data_to_be_created (schema.CommentCreate): 작성될 comment의 내용
        - current_user (User, optional): 현재 로그인된 user의 정보

    Raises:
        - HTTPException (401 UNAUTHORIZED): writer_id와 current_user의 id가 다를 경우
        - HTTPException (404 NOT FOUND): 다음 2가지 경우에 발생한다.
            - post_id에 해당되는 post가 존재하지 않는 경우
            - writer_id에 해당되는 회원이 없을 경우
        - HTTPException (500 INTERNAL SERVER ERROR): comment 생성에 실패할 경우

    Returns:
        - Comment: 생성된 comment 정보를 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=writer_id,
    )
    user_service.check_if_user_is_none(selected_user)
    post_service.get_post_and_check_none(
        db,
        post_id=post_id,
    )
    comment = comment_service.create_comment(
        db,
        writer_id,
        current_user,
        post_id,
        data_to_be_created.dict(),
    )
    return comment


@router.put(
    "/users/{writer_id}/comments/{comment_id}",
    response_model=schema.Comment,
    status_code=status.HTTP_200_OK,
)
def update_comment(
    writer_id: int,
    comment_id: int,
    data_to_be_updated: schema.CommentUpdate,
    current_user: User = Depends(UserService.get_current_user_verified),
    user_service: UserService = Depends(UserService),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> schema.Comment:
    """전달된 정보로 comment를 수정한다.

    Args:
        - writer_id (int): comment를 작성했던 user의 id
        - comment_id (int): 수정할 comment의 id
        - data_to_be_updated (schema.CommentUpdate): 변경될 내용
        - current_user (User, optional): 현재 로그인된 user의 정보

    Raises:
        - HTTPException (401 UNAUTHORIZED): user_id와 current_user의 id가 다를 경우 발생하는 에러
        - HTTPException (404 NOT FOUND): user_id에 해당되는 회원이 없을 경우
        - HTTPException (500 INTERNAL SERVER ERROR): comment 수정에 실패할 경우

    Returns:
        - Comment: 수정된 comment 정보를 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=writer_id,
    )
    user_service.check_if_user_is_none(selected_user)
    comment = comment_service.update_comment(
        db,
        writer_id,
        current_user,
        comment_id,
        data_to_be_updated.dict(),
    )

    return comment


@router.delete(
    "/users/{writer_id}/comments/{comment_id}",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def delete_comment(
    writer_id: int,
    comment_id: int,
    current_user: User = Depends(UserService.get_current_user_verified),
    user_service: UserService = Depends(UserService),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> Msg:
    """전달된 정보에 해당되는 comment를 삭제한다.

    Args:
        - writer_id (int): comment를 작성했던 user의 id
        - comment_id (int): 삭제할 comment의 id
        - current_user (User): 현재 로그인된 user의 정보

    Raises:
        - HTTPException (401 UNAUTHORIZED): user_id와 current_user의 id가 다를 경우 발생하는 에러
        - HTTPException (404 NOT FOUND): user_id에 해당되는 회원이 없을 경우
        - HTTPException (500 INTERNAL SERVER ERROR): comment 삭제에 실패할 경우

    Returns:
        - schema.Msg: 삭제 성공 메세지를 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=writer_id,
    )
    user_service.check_if_user_is_none(selected_user)
    comment_service.delete_comment(
        db,
        writer_id,
        current_user,
        comment_id,
    )
    return {"status": "success", "msg": "댓글이 삭제되었습니다."}
