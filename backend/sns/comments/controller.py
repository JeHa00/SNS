from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import get_current_user_verified
from sns.users.model import User
from sns.users.schema import Msg
from sns.comments.schema import Comment, CommentCreate, CommentUpdate


router = APIRouter()


@router.get("/posts/{post_id}/comments", response_model=List[Comment], status_code=status.HTTP_200_OK)
def get_comments_on_a_post(
    post_id: int,
    db: Session = Depends(db.get_db)
):
    pass


@router.get("/users/{user_id}/comments", response_model=List[Comment], status_code=status.HTTP_200_OK)
def get_comments_of_a_user(
    post_id: int, 
    db: Session = Depends(db.get_db)
):
    pass


@router.get("/posts/{post_id}/comments/{comment_id}", response_model=Comment, status_code=status.HTTP_200_OK)
def get_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(db.get_db)
):
    pass


@router.post("/posts/{post_id}/comments", response_model=Comment, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    data_to_be_created: CommentCreate,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    pass


@router.put("/posts/{post_id}/comments/{comment_id}", response_model=Comment, status_code=status.HTTP_200_OK)
def update_comment(
    post_id: int,
    comment_id: int,
    data_to_be_updated: CommentUpdate, 
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    pass


@router.delete("/posts/{post_id}/comments/{comment_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    pass