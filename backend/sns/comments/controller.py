from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import get_current_user_verified
from sns.users.model import User
from sns.users.schema import Msg
from sns.posts.service import get_post
from sns.comments.schema import Comment, CommentCreate, CommentUpdate
from sns.comments.repository import comment_crud
from sns.comments import model


router = APIRouter()


@router.get(
    "/posts/{post_id}/comments",
    response_model=List[Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_on_a_post(
    post_id: int,
    db: Session = Depends(db.get_db),
) -> List[model.Comment]:
    """**한 개의 post에 대한 모든 comment를 조회한다.**

    **Args:**
        - post_id (int): comment가 달린 post의 id

    **Raises:**
        - HTTPException(404 NOT FOUND): id에 해당되는 post가 없을 때 발생하는 에러

    **Returns:**
        - List[model.Comment]: 해당되는 여러 comment를 list에 담겨 반환
    """
    selected_post = get_post(db, post_id=post_id)
    if selected_post:
        comments = comment_crud.get_multi_comments(db, post_id=post_id)
        return comments
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 id의 포스트를 찾을 수 없습니다.",
        )


@router.get(
    "/users/{user_id}/comments",
    response_model=List[Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_of_a_user(
    user_id: int,
    db: Session = Depends(db.get_db),
) -> List[Comment]:
    """**한 user가 작성한 모든 comment를 조회한다.**

    **Args:**
        - user_id (int): comment를 작성한 user의 id

    **Raises:**
        - HTTPException(404 NOT FOUND): user_id에 해당되는 user가 작성한 댓글이 없으면 발생하는 에러
        - HTTPException(403 FORBIDDEN): user_id로 등록된 회원이 없으면 발생하는 에러

    **Returns:**
        - List[model.Comment]: 해당되는 여러 comment를 list에 담겨 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        comments = comment_crud.get_multi_comments(db, writer_id=user_id)
        if len(comments) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작성된 댓글이 없습니다.",
            )
        else:
            return comments
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="등록된 회원이 아닙니다.",
        )


@router.post(
    "/users/{user_id}/posts/{post_id}/comments",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    user_id: int,
    post_id: int,
    data_to_be_created: CommentCreate,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Comment:
    """**전달된 정보로 comment를 생성한다.**

    **Args:**
        - user_id (int): comment를 생성할 user의 id
        - post_id (int): comment가 작성될 post의 id
        - data_to_be_created (CommentCreate): 작성될 comment의 내용
        - current_user (User, optional): 현재 로그인된 user의 정보

    **Raises:**
        - HTTPException(401 UNAUTHORIZED): user_id와 current_user의 id가 다를 경우 발생하는 에러
        - HTTPException(403 FORBIDDEN): user_id로 등록된 회원이 없으면 발생하는 에러

    **Returns:**
        - Comment: 생성된 comment 정보를 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            comment = comment_crud.create(
                db,
                data_to_be_created=data_to_be_created,
                writer_id=user_id,
                post_id=post_id,
            )
            return comment
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="작성할 권한이 없습니다.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="등록된 회원이 아닙니다.",
        )


@router.put(
    "/users/{user_id}/comments/{comment_id}",
    response_model=Comment,
    status_code=status.HTTP_200_OK,
)
def update_comment(
    user_id: int,
    comment_id: int,
    data_to_be_updated: CommentUpdate,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Comment:
    """**전달된 정보로 comment를 수정한다.**

    **Args:**
        - user_id (int): comment를 작성했던 user의 id
        - comment_id (int): 수정할 comment의 id
        - data_to_be_updated (CommentUpdate): 변경될 내용
        - current_user (User, optional): 현재 로그인된 user의 정보

    **Raises:**
        - HTTPException(401 UNAUTHORIZED): user_id와 current_user의 id가 다를 경우 발생하는 에러
        - HTTPException(403 FORBIDDEN): user_id로 등록된 회원이 없으면 발생하는 에러

    **Returns:**
        - Comment: 수정된 comment 정보를 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            comment = comment_crud.update(
                db,
                comment_info=comment_id,
                data_to_be_updated=data_to_be_updated,
            )
            return comment
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="수정할 권한이 없습니다.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="등록된 회원이 아닙니다.",
        )


@router.delete(
    "/users/{user_id}/comments/{comment_id}",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def delete_comment(
    user_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """**전달된 정보에 해당되는 comment를 삭제한다.**

    **Args:**
        - user_id (int): comment를 작성했던 user의 id
        - comment_id (int): 삭제할 comment의 id
        - current_user (User, optional): 현재 로그인된 user의 정보

    **Raises:**
        - HTTPException(401 UNAUTHORIZED): user_id와 current_user의 id가 다를 경우 발생하는 에러
        - HTTPException(403 FORBIDDEN): user_id로 등록된 회원이 없으면 발생하는 에러

    **Returns:**
        - schema.Msg: 삭제 성공 메세지를 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            comment_crud.remove(db, comment_info=comment_id)
            return {"status": "success", "msg": "댓글이 삭제되었습니다."}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="삭제할 권한이 없습니다.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="등록된 회원이 아닙니다.",
        )
