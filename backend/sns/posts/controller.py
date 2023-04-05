from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import get_current_user_verified, get_user
from sns.users.schema import Msg, UserBase
from sns.users.model import User
from sns.posts.schema import Post
from sns.posts import model
from sns.posts.service import (
    get_multi_posts,
    get_post,
    create,
    update,
    remove
)


router = APIRouter()


@router.get("/posts/{post_id}", response_model=Post, status_code=status.HTTP_200_OK)
def read_post(
    post_id: int,
    db: Session = Depends(db.get_db)
) -> model.Post:
    """post_id와 일치하는 post.id를 가진 post 정보를 읽어온다.

    Args:
        post_id (int): 읽어올 post의 id

    Returns:
        model.Post: post model 객체를 반환
    """

    # post.id가 post_id인 post 정보를 읽어온다.
    post = get_post(db, post_id=post_id)    
    
    if not post:
        raise HTTPException(status_code=404, detail="해당 id의 포스트를 찾을 수 없습니다.")        
    else:
        return post


@router.get("/users/{user_id}/posts", response_model=List[Post], status_code=status.HTTP_200_OK)
def read_posts(
    user_id: int,
    db: Session = Depends(db.get_db)
):
    # user.id가 user_id인 writer의 post들을 모두 가져온다.
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        posts = get_multi_posts(db, writer_id=user_id)
        if len(posts) == 0:
            raise HTTPException(status_code=404, detail="생성된 글이 없습니다.")
        else:
            return posts
    else:
        raise HTTPException(status_code=404, detail="등록되지 않은 유저입니다.")

@router.post("/users/{user_id}/posts/{post_id}", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(
    content: str, 
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    # 현재 로그인되어 있는 유저가 글을 추가한다.
    pass 


@router.put("/users/{user_id}/posts/{post_id}", response_model=Post, status_code=status.HTTP_200_OK)
def update_post(
    user_id: int,
    post_id: int,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    # post.id가 post_id인 post를 편집한다. 이 때 current_user일 때만 가능하다.
    pass 


@router.delete("/users/{user_id}/posts/{post_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_post(
    user_id: int, 
    post_id: int,
    current_user: UserBase = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
) -> dict:
    """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

    Args:
        user_id (int): user의 id
        post_id (int): post의 id
        current_user (UserBase): 현재 로그인된 유저

    Returns:
        schema.Msg: 삭제 성공 메세지를 반환
    """  

    if user_id == current_user.id:
        remove(db, post_info=post_id)
        return {"status": "success", "msg": "글이 삭제되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="삭제할 권한이 없습니다."
        )