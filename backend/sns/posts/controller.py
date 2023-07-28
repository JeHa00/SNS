from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.schema import Msg, UserBase
from sns.users.service import user_service
from sns.users.model import User
from sns.posts.schema import Post, PostCreate, PostUpdate, PostLike, PostUnlike
from sns.posts.service import post_service, post_like_service
from sns.posts import model


router = APIRouter()


@router.get("/posts/likees", response_model=List[Post], status_code=status.HTTP_200_OK)
def read_likees(
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> List[Post]:
    """current_user에게 좋아요를 받은 likee인 post들을 조회한다.

    Args:

    - current_user (User, optional): 현재 로그인된 user 정보

    Returns:

    - List[Post]: like를 받은 post 목록을 반환
    """
    posts = post_like_service.get_like_targets(db, who_like_id=current_user.id)
    return posts


@router.get(
    "/posts/{post_id}/likers",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_likers(post_id: int, db: Session = Depends(db.get_db)) -> List[UserBase]:
    """post_id에 해당하는 post를 좋아요한 liker들인 user를 조회한다.

    Args:

    - post_id (int): 좋아요를 받은 post

    Returns:

    - List[UserBase]: post를 좋아요한 유저 목록을 반환
    """
    likers = post_like_service.get_users_who_like(db, like_target_id=post_id)
    return likers


@router.post(
    "/posts/{post_id}/like",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def like_post(
    post_id: int,
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """현재 로그인되어있는 user가 post_id에 해당하는 post를 like 한다.

    Args:

    - post_id (int): current_user로부터 like를 받을 post
    - current_user (User, optional): 현재 로그인된 user 정보

    Returns:

    - Msg: post 좋아요 성공 메세지를 반환
    """
    like_data = PostLike(who_like_id=current_user.id, like_target_id=post_id)
    post_like_service.like(db, like_data=like_data)
    return {"status": "success", "msg": "post 좋아요가 완료되었습니다."}


@router.post(
    "/posts/{post_id}/unlike",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def unlike_post(
    post_id: int,
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """현재 로그인되어있는 user가 post_id에 해당하는 post의 like를 취소한다.
        이는 is_liked 값을 false로 바꾼다.

    Args:

    - post_id (int): _description_
    - current_user (User, optional): 현재 로그인된 user 정보

    Returns:

    - Msg: post 좋아요 취소 성공 메세지를 반환
    """
    unlike_data = PostUnlike(who_like_id=current_user.id, like_target_id=post_id)
    post_like_service.unlike(db, unlike_data=unlike_data)
    return {"status": "success", "msg": "post 좋아요가 취소되었습니다"}


@router.get("/posts/{post_id}", response_model=Post, status_code=status.HTTP_200_OK)
def read_post(post_id: int, db: Session = Depends(db.get_db)) -> model.Post:
    """post_id와 일치하는 post.id를 가진 post 정보를 읽어온다.

    Args:

    - post_id (int): 읽어올 post의 id

    Raises:

    - HTTPException(404 NOT FOUND): post_id에 해당되는 post를 찾을 수 없을 때 발생

    Returns:

    - Post: post_id에 해당되는 post 반환
    """
    post = post_service.get_post(db, post_id=post_id)
    return post


@router.get(
    "/users/{user_id}/posts",
    response_model=List[Post],
    status_code=status.HTTP_200_OK,
)
def read_posts(
    user_id: int,
    user_service=Depends(user_service),
    post_service=Depends(post_service),
    db: Session = Depends(db.get_db),
) -> List[Post]:
    """user_id에 일치하는 user가 작성한 글들을 조회

    Args:

     - user_id (int): user의 id

    Raises:

    - HTTPException(404 NOT FOUND): 다음 2가지 경우에 대해서 발생한다.
        - post_id에 해당되는 post가 찾을 수 없을 때 발생
        - writer_id에 해당되는 user가 단 하나의 post도 작성하지 않았을 때 발생

    Returns:

     - List[Post]: 여러 post가 list 배열에 담겨져 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(selected_user)
    posts = post_service.get_multi_posts(
        db,
        writer_id=selected_user.id,
    )
    return posts


@router.post(
    "/users/{user_id}/posts",
    response_model=Post,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    user_id: int,
    data_to_be_created: PostCreate,
    user_service=Depends(user_service),
    post_service=Depends(post_service),
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Post:
    """user_id가 현재 로그인된 user와 동일할 때 post를 생성한다.

    Args:

    - user_id (int): 글을 작성할 user의 id
    - data_to_be_created (PostCreate): 생성할 post의 content 정보
    - current_user (User, optional): 현재 로그인된 user 정보

    Raises:

    - HTTPException(404 NOT FOUND): post_id에 해당되는 post가 찾을 수 없을 때 발생
    - HTTPException(500 INTERNAL SERVER ERROR): post 생성에 실패했을 때 발생
    - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없음을 보여주는 에러

    Returns:

    - Post: 생성된 post 정보 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_user_is_none(user)
    post = post_service.create_post(
        db,
        user_id,
        data_to_be_created,
        current_user,
    )
    return post


@router.put(
    "/users/{user_id}/posts/{post_id}",
    response_model=Post,
    status_code=status.HTTP_200_OK,
)
def update_post(
    user_id: int,
    post_id: int,
    data_to_be_updated: PostUpdate,
    user_service=Depends(user_service),
    post_service=Depends(post_service),
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Post:
    """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 post를 수정한다.

    Args:

    - user_id (int): 수정할 user의 id
    - post_id (int): 수정될 post의 id
    - data_to_be_updated (PostUpdate): 업데이트할 정보
    - current_user (User): 현재 유저 정보

    Raises:

    - HTTPException(404 NOT FOUND): 다음 2가지 경우에 대해서 발생한다.
        - user_id에 해당되는 user를 찾을 수 없을 때 발생
        - post_id에 해당되는 post를 찾을 수 없을 때 발생
    - HTTPException(500 INTERNAL SERVER ERROR): post 정보 변경에 실패했을 때 발생
    - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 유저 id와 달라 수정 권한이 없음을 보여주는 에러

    Returns:

    - Post: 수정된 post 객체 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_user_is_none(user)
    post = post_service.update_post(
        db,
        user_id,
        post_id,
        data_to_be_updated,
        current_user,
    )
    return post


@router.delete(
    "/users/{user_id}/posts/{post_id}",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def delete_post(
    user_id: int,
    post_id: int,
    user_service=Depends(user_service),
    post_service=Depends(post_service),
    current_user: User = Depends(user_service.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

    Args:

    - user_id (int): 삭제시킬 user의 id
    - post_id (int): 삭제될 post의 id
    - current_user (User): 현재 로그인된 user 정보

    Raises:

    - HTTPException(404 NOT FOUND): 다음 2가지 경우에 대해서 발생한다.
        - user_id에 해당되는 user를 찾을 수 없을 때 발생
        - post_id에 해당되는 post를 찾을 수 없을 때 발생
    - HTTPException(500 INTERNAL SERVER ERROR): post 삭제에 실패했을 때 발생
    - HTTPException(401 UNAUTHORIZED): user_id가 로그인된 유저 id와 달라 삭제 권한이 없음을 보여주는 에러

    Returns:

    - Msg: 삭제 성공 메세지를 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_user_is_none(user)
    post_service.delete_post(
        db,
        user_id,
        post_id,
        current_user,
    )
    return {"status": "success", "msg": "글이 삭제되었습니다."}
