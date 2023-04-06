from typing import List

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.service import get_current_user_verified
from sns.users.schema import Msg
from sns.users.model import User
from sns.posts.schema import Post, PostCreate, PostUpdate
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
        Post: post_id에 해당되는 post 반환  
    """
    post = get_post(db, post_id=post_id)    
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당 id의 포스트를 찾을 수 없습니다.")        
    else:
        return post


@router.get("/users/{user_id}/posts", response_model=List[Post], status_code=status.HTTP_200_OK)
def read_posts(
    user_id: int,
    db: Session = Depends(db.get_db)
):
    """user_id에 일치하는 user가 작성한 post들을 조회

    Args:    
        user_id (int): user의 id

    Returns:  
        List[Post]: 여러 post가 list 배열에 담겨져 반환  
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        posts = get_multi_posts(db, writer_id=user_id)
        if len(posts) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="작성된 글이 없습니다.")
        else:
            return posts
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다.")


@router.post("/users/{user_id}/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(
    user_id: int, 
    data_to_be_created: PostCreate,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    """user_id가 현재 로그인된 user와 동일할 때 post를 생성한다.

    Args:
        user_id (int): 글을 작성할 user의 id
        data_to_be_created (PostCreate): 생성할 post의 content 정보
        current_user (User, optional): 현재 로그인된 user 정보

    Returns:
       Post: 생성된 post 정보 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if user_id == current_user.id:
            post = create(db, post_info=data_to_be_created, writer_id=user_id)
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="작성할 권한이 없습니다."
            )
    else: 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다.")


@router.put("/users/{user_id}/posts/{post_id}", response_model=Post, status_code=status.HTTP_200_OK)
def update_post(
    user_id: int,
    post_id: int,
    data_to_be_updated: PostUpdate, 
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 post를 수정한다.

    Args:
        user_id (int): 수정할 user의 id
        post_id (int): 수정될 post의 id
        data_to_be_updated (PostUpdate): _description_
        current_user (User, optional): _description_. Defaults to Depends(get_current_user_verified).
        db (Session, optional): _description_. Defaults to Depends(db.get_db).

    Raises:
        HTTPException: _description_
        HTTPException: _description_
        HTTPException: _description_

    Returns:
        Post: 수정된 post 정보 반환
    """
    selected_user = db.query(User).filter(User.id == user_id).first()
    if selected_user:
        if selected_user.id == current_user.id:
            post = get_post(db, post_id=post_id)
            if not post:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="해당되는 글이 없습니다.")
            else:
                update(db, post_info=post, data_to_be_updated=data_to_be_updated)
                return post
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="작성할 권한이 없습니다."
            )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="등록된 회원이 아닙니다.")


@router.delete("/users/{user_id}/posts/{post_id}", response_model=Msg, status_code=status.HTTP_200_OK)
def delete_post(
    user_id: int, 
    post_id: int,
    current_user: User = Depends(get_current_user_verified),
    db: Session = Depends(db.get_db)
):
    """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

    Args:  
        user_id (int): 삭제시킬 user의 id  
        post_id (int): 삭제될 post의 id  
        current_user (User): 현재 로그인된 user 정보
  
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