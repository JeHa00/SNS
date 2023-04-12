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


router = APIRouter()


@router.get(
    "/posts/{post_id}/comments",
    response_model=List[Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_on_a_post(post_id: int, db: Session = Depends(db.get_db)):
    selected_post = get_post(db, post_id=post_id)
    if selected_post:
        comments = comment_crud.get_multi_comments(db, post_id=post_id)
        return comments
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="해당 id의 포스트를 찾을 수 없습니다."
        )


@router.get(
    "/users/{user_id}/comments",
    response_model=List[Comment],
    status_code=status.HTTP_200_OK,
)
def get_comments_of_a_user(user_id: int, db: Session = Depends(db.get_db)):
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        comments = comment_crud.get_multi_comments(db, writer_id=user_id)
        if len(comments) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="작성된 댓글이 없습니다."
            )
        else:
            return comments
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다."
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
):
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
                status_code=status.HTTP_401_UNAUTHORIZED, detail="작성할 권한이 없습니다."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다."
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
):
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            comment = comment_crud.update(
                db, comment_info=comment_id, data_to_be_updated=data_to_be_updated
            )
            return comment
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="수정할 권한이 없습니다."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다."
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
):
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            comment_crud.remove(db, comment_info=comment_id)
            return {"status": "success", "msg": "댓글이 삭제되었습니다."}
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="삭제할 권한이 없습니다."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다."
        )
