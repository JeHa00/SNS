from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import UserService
from sns.users.schema import Message, UserBase
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
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> List[schema.Comment]:
    """post_id에 해당하는 글에 작성된 댓글들을 조회한다.
        한 번 조회시 최대 30개를 조회한다. 다음 30개 댓글을 조회하고 싶다면 page 매개변수를 통해 조절한다.

    Args:

    - post_id (int): 작성된 글의 id
    - page (int): offset 하기 위한 page

    Raises:

    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 글이 없을 경우 (code: POST_NOT_FOUND)
    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우 (code: COMMENT_NOT_FOUND)

    Returns:

    - List[schema.Comment]: 댓글 정보들이 배열에 담겨진 형태로 반환
    """
    return comment_service.get_comments_on_a_post(db, post_id, page)


@router.get(
    "/users/{user_id}/comments",
    response_model=List[schema.Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_of_a_user(
    user_id: int,
    page: int,
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> List[schema.Comment]:
    """user_id에 해당되는 유저가 작성한 댓글들을 조회한다.
    한 번 조회시 최대 30개를 조회한다. 다음 30개를 조회하고 싶다면 page 매개변수를 통해 조절한다.

    Args:

    - user_id (int): 유저의 id
    - page (int): 조회 시 offset 하기 위한 page

    Raises:

    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 유저가 없을 경우 (code: USER_NOT_FOUND)
    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우 (code: COMMENT_NOT_FOUND)

    Returns:

    - List[Comment]: 여러 댓글 정보들이 배열에 담겨진 형태로 반환
    """
    return comment_service.get_comments_of_a_user(db, user_id, page)


@router.post(
    "/users/{writer_id}/posts/{post_id}/comment",
    response_model=schema.Comment,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    writer_id: int,
    post_id: int,
    data_to_be_created: schema.CommentCreate,
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> schema.Comment:
    """writer_id와 jwt로 받은 유저의 id가 같을 때 data_to_be_created에 담겨진 내용으로 댓글을 작성한다.

    Args:

    - writer_id (int): 작성하려는 유저의 id
    - post_id (int): 댓글이 작성되는 글의 id
    - data_to_be_created (schema.CommentCreate): 댓글의 내용 content

    Raises:

    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 유저가 없을 경우 (code: USER_NOT_FOUND)
    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 글이 없을 경우 (code: POST_NOT_FOUND)
    - HTTPException (403 FORBIDDEN): writer_id가 로그인된 유저의 id와 달라 작성 권한이 없으면 발생
    - HTTPException (500 INTERNAL SERVER ERROR): 댓글 생성에 실패하면 발생

    Returns:

    - schema.Comment: 생성된 댓글 정보를 반환
    """
    return comment_service.create_comment(
        db,
        writer_id,
        current_user.id,
        post_id,
        data_to_be_created,
    )


@router.put(
    "/comments/{comment_id}",
    response_model=schema.Comment,
    status_code=status.HTTP_200_OK,
)
def update_comment(
    comment_id: int,
    data_to_be_updated: schema.CommentUpdate,
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> schema.Comment:
    """comment_id에 해당되는 댓글 작성자가 jwt로부터 얻은 유저의 id와 같을 경우
       data_to_be_updated에 담겨진 내용으로 댓글을 수정한다.

    Args:

    - comment_id (int): 댓글의 id
    - data_to_be_updated (schema.CommentUpdate): 수정하려는 댓글의 내용 content

    Raises:

    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우 (code: COMMENT_NOT_FOUND)
    - HTTPException (403 FORBIDDEN): 댓글의 작성자가 로그인한 유저의 id와 달라 수정 권한이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 댓글 수정에 실패했을 때 발생

    Returns:

    - schema.Comment: 수정된 댓글 정보를 반환
    """
    return comment_service.update_comment(
        db,
        current_user.id,
        comment_id,
        data_to_be_updated.dict(),
    )


@router.delete(
    "/comments/{comment_id}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def delete_comment(
    comment_id: int,
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    comment_service: CommentService = Depends(CommentService),
    db: Session = Depends(db.get_db),
) -> Message:
    """comment_id에 해당되는 댓글 작성자가 jwt로부터 얻은 유저의 id와 같을 경우 댓글을 삭제한다.

    Args:

    - comment_id (int): 댓글의 id

    Raises:

    - HTTPException (404 NOT FOUND): 주어진 정보에 해당되는 댓글이 없을 경우 (code: COMMENT_NOT_FOUND)
    - HTTPException (403 FORBIDDEN): 댓글의 작성자가 로그인한 유저의 id와 달라 삭제 권한이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 댓글 삭제에 실패했을 때 발생

    Returns:

    - Msg: 삭제 성공 시 성공 메세지를 반환
    """
    comment_service.delete_comment(
        db,
        current_user.id,
        comment_id,
    )
    return {"status": "success", "msg": "댓글이 삭제되었습니다."}
