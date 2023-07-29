from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from sns.common.session import db
from sns.users.schema import Msg, UserBase
from sns.users.service import UserService
from sns.users.model import User
from sns.posts.service import PostService
from sns.posts import schema


router = APIRouter()


@router.get(
    "/posts/likees",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_likees(
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """current_user에게 좋아요를 받은 likee인 post들을 조회한다.

    Raises:

    - HTTPException (404 NOT FOUND): 해당 유저가 좋아요를 한 글이 없으면 발생

    Returns:

    - List[Post]: like를 받은 post 목록을 반환
    """
    return post_service.get_like_targets(db, current_user.id)


@router.get(
    "/posts/{post_id}/likers",
    response_model=List[UserBase],
    status_code=status.HTTP_200_OK,
)
def read_likers(
    post_id: int,
    post_service: PostService = Depends(PostService),
    db: Session = Depends(db.get_db),
) -> List[UserBase]:
    """post_id에 해당하는 post를 좋아요한 liker들인 user를 조회한다.

    Args:

    - post_id (int): 좋아요를 받은 post


    Raises:

    - HTTPException (404 NOT FOUND): 해당 post에 좋아요를 한 user들이 없으면 발생

    Returns:

    - List[UserBase]: post를 좋아요한 유저 목록을 반환
    """
    return post_service.get_users_who_like(db, post_id)


@router.post(
    "/posts/{post_id}/like",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def like_post(
    post_id: int,
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """현재 로그인되어있는 user가 post_id에 해당하는 post를 like 한다.

    Args:

    - post_id (int): current_user로부터 like를 받을 post의 id

    Raises:

    - HTTPException (400 BAD REQUEST): 이미 is_liked 상태 값이 True이면 발생
    - HTTPException (500 INTERNAL SERVER ERROR): post 좋아요 작업에 실패하면 발생

    Returns:

    - Msg: post 좋아요 성공 메세지를 반환
    """
    post_service.like(db, post_id, current_user.id)
    return {"status": "success", "msg": "post 좋아요가 완료되었습니다."}


@router.post(
    "/posts/{post_id}/unlike",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
)
def unlike_post(
    post_id: int,
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """현재 로그인되어있는 user가 post_id에 해당하는 post의 like를 취소한다.
        이는 is_liked 값을 false로 바꾼다.

    Args:

    - post_id (int): current_user로부터 like를 취소받을 post의 id

    Raises:

    - HTTPException (400 BAD REQUEST): 이미 is_liked 상태 값이 False이면 발생
    - HTTPException (500 INTERNAL SERVER ERROR): post 좋아요 취소 작업에 실패하면 발생

    Returns:

    - Msg: post 좋아요 취소 성공 메세지를 반환
    """
    post_service.unlike(db, post_id, current_user.id)
    return {"status": "success", "msg": "post 좋아요가 취소되었습니다"}


@router.get(
    "/posts/{post_id}",
    response_model=schema.Post,
    status_code=status.HTTP_200_OK,
)
def read_post(
    post_id: int,
    post_service: PostService = Depends(PostService),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """post_id와 일치하는 post.id를 가진 post 정보를 읽어온다.

    Args:

    - post_id (int): 읽어올 post의 id

    Raises:

    - HTTPException (404 NOT FOUND): post_id에 해당되는 post를 찾을 수 없을 때 발생

    Returns:

    - Post: post_id에 해당되는 post 반환
    """
    return post_service.get_post_and_check_none(db, post_id=post_id)


# NOTE: 10개씩 이어서 가져오는지 확인
@router.get(
    "/users/{user_id}/posts",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_posts(
    user_id: int,
    user_service: UserService = Depends(UserService),
    post_service: PostService = Depends(PostService),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """user_id에 일치하는 user가 작성한 글들을 조회

    Args:

     - user_id (int): user의 id

    Raises:

    - HTTPException (404 NOT FOUND): 다음 경우에 대해서 발생한다.
        - writer_id에 해당되는 user가 단 하나의 post도 작성하지 않았을 때 발생

    Returns:

     - List[Post]: 여러 post가 list 배열에 담겨져 반환
    """
    selected_user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(selected_user)
    posts = post_service.get_multi_posts_and_check_none(
        db,
        writer_id=selected_user.id,
    )
    return posts


@router.post(
    "/users/{user_id}/posts",
    response_model=schema.Post,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    user_id: int,
    data_to_be_created: schema.PostCreate,
    user_service: UserService = Depends(UserService),
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """user_id가 현재 로그인된 user와 동일할 때 post를 생성한다.

    Args:

    - user_id (int): 글을 작성할 user의 id
    - data_to_be_created (PostCreate): 생성할 post의 content 정보

    Raises:

    - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 user id와 달라 작성 권한이 없음을 보여주는 에러
    - HTTPException (404 NOT FOUND): post_id에 해당되는 post가 찾을 수 없을 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): post 생성에 실패했을 때 발생

    Returns:

    - Post: 생성된 post 정보 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(user)
    post = post_service.create_post(
        db,
        user_id,
        current_user,
        data_to_be_created.dict(),
    )
    return post


@router.patch(
    "/users/{user_id}/posts/{post_id}",
    response_model=schema.Post,
    status_code=status.HTTP_200_OK,
)
def update_post(
    user_id: int,
    post_id: int,
    data_to_be_updated: schema.PostUpdate,
    user_service: UserService = Depends(UserService),
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 post를 수정한다.

    Args:

    - user_id (int): 수정할 user의 id
    - post_id (int): 수정될 post의 id
    - data_to_be_updated (PostUpdate): 업데이트할 정보
        - content

    Raises:

    - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 유저 id와 달라 수정 권한이 없음을 보여주는 에러
    - HTTPException (404 NOT FOUND): 다음 2가지 경우에 대해서 발생한다.
        - user_id에 해당되는 user를 찾을 수 없을 때 발생
        - post_id에 해당되는 post를 찾을 수 없을 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): post 정보 변경에 실패했을 때 발생

    Returns:

    - Post: 수정된 post 객체 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(user)
    post = post_service.update_post(
        db,
        user_id,
        post_id,
        current_user,
        data_to_be_updated.dict(),
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
    user_service: UserService = Depends(UserService),
    post_service: PostService = Depends(PostService),
    current_user: User = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Msg:
    """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

    Args:

    - user_id (int): 삭제시킬 user의 id
    - post_id (int): 삭제될 post의 id

    Raises:

    - HTTPException (401 UNAUTHORIZED): user_id가 로그인된 유저 id와 달라 삭제 권한이 없음을 보여주는 에러
    - HTTPException (404 NOT FOUND): 다음 2가지 경우에 대해서 발생한다.
        - user_id에 해당되는 user를 찾을 수 없을 때 발생
        - post_id에 해당되는 post를 찾을 수 없을 때 발생
    - HTTPException (500 INTERNAL SERVER ERROR): post 삭제에 실패했을 때 발생

    Returns:

    - Msg: 삭제 성공 메세지를 반환
    """
    user = user_service.get_user(
        db,
        user_id=user_id,
    )
    user_service.check_if_user_is_none(user)
    post_service.delete_post(
        db,
        user_id,
        post_id,
        current_user,
    )
    return {"status": "success", "msg": "글이 삭제되었습니다."}
