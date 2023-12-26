from typing import List

from fastapi import APIRouter, Depends, status
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.common.session import db, redis_db
from sns.users.schema import Message, UserRead, UserBase
from sns.users.service import UserService
from sns.posts.service import PostService
from sns.posts import schema


router = APIRouter()


@router.get(
    "/posts/liked_posts",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_liked_posts(
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """현재 로그인한 유저가 좋아요한 글들을 조회한다.

    Raises:

    - HTTPException (404 NOT FOUND): 해당 유저가 좋아요를 한 글이 없는 경우

    Returns:

    - List[Post]: like를 받은 post 목록을 반환
    """
    return post_service.read_liked_posts(
        db,
        current_user.id,
    )


@router.get(
    "/posts/followers",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_posts_of_followers(
    page: int,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """현재 로그인한 유저의 팔로워 유저들이 작성한 글들을 조회한다.
        작성된 글들은 생성 날짜를 기준으로 정렬되어 받는다.

    Args:

    - page (int): 조회할 page 번호.

    Returns:

    -  List[Post]: 조회된 글들의 목록
    """
    return post_service.read_posts_of_followers(
        db,
        current_user.id,
        page,
    )


@router.get(
    "/posts/{post_id}/users_who_like",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
)
def read_users_who_like(
    post_id: int,
    background_tasks: BackgroundTasks,
    post_service: PostService = Depends(),
    redis_db: Redis = Depends(redis_db.get_db),
    db: Session = Depends(db.get_db),
) -> List[UserRead]:
    """post_id에 해당하는 글에 좋아요한 user들을 조회한다.

    Args:

    - post_id (int): 좋아요를 받은 글

    Raises:

    - HTTPException(404 NOT FOUND): 다음 2가지 경우에 발생한다.
        - post_id에 해당하는 post를 조회하지 못한 경우 (code: POST_NOT_FOUND)
        - 해당 글에 좋아요를 한 user들이 없는 경우 (code: USER_WHO_LIKE_NOT_FOUND)

    Returns:

    - List[UserRead]: post를 좋아요한 유저 목록을 반환
    """
    return post_service.read_users_who_like(
        db,
        redis_db,
        post_id,
        background_tasks,
    )


@router.post(
    "/posts/{post_id}/like",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    redis_db: Redis = Depends(redis_db.get_db),
    db: Session = Depends(db.get_db),
) -> Message:
    """현재 로그인한 user가 post_id에 해당하는 글에 좋아요를 한다.

    Args:

    - post_id (int): 현재 로그인된 user로부터 좋아요를 받을 글의 id

    Raises:

    - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생
        - 글 좋아요에 실패한 경우 (code: FAILED_TO_LIKE_POST)
        - 알림 생성에 실패한 경우 (code: FAILED_TO_CREATE_NOTIFICATION)

    Returns:

    - Message: post 좋아요 성공 메세지를 반환
    """
    post_service.like_post(
        db,
        redis_db,
        background_tasks,
        post_id,
        current_user.id,
    )
    return {"status": "success", "message": "post 좋아요가 완료되었습니다."}


@router.post(
    "/posts/{post_id}/unlike",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def unlike_post(
    post_id: int,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Message:
    """현재 로그인한 user가 post_id에 해당하는 글의 좋아요를 취소한다.

    Args:

    - post_id (int): 현재 로그인한 user로부터 좋아요를 취소받을 글의 id

    Raises:

    - HTTPException (404 NOT FOUND): 다음 2가지 경우에 발생한다.
        - post_id에 해당하는 글이 없는 경우 (code: POST_NOT_FOUND)
        - 주어진 정보에 해당하는 PostLike 정보가 없는 경우 (code: POST_LIKE_NOT_FOUND)
    - HTTPException (500 INTERNAL SERVER ERROR): 좋아요 취소 작업에 실패한 경우

    Returns:

    - Message: post 좋아요 취소 성공 메세지를 반환
    """
    post_service.unlike_post(db, post_id, current_user.id)
    return {"status": "success", "message": "post 좋아요가 취소되었습니다"}


@router.get(
    "/posts/{post_id}",
    response_model=schema.Post,
    status_code=status.HTTP_200_OK,
)
def read_post(
    post_id: int,
    post_service: PostService = Depends(),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """post_id와 일치하는 글 정보를 조회한다.

    Args:

    - post_id (int): 읽어올 글의 id

    Raises:

    - HTTPException (404 NOT FOUND): post_id에 해당되는 글을 찾을 수 없을 때 발생

    Returns:

    - Post: post_id에 해당되는 글을 반환
    """
    return post_service.read_post(db, post_id=post_id)


@router.get(
    "/posts",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_posts(
    page: int,
    post_service: PostService = Depends(),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """전체 글 목록을 조회한다. 하나도 없을 경우 404 에러를 일으킨다.

    Args:

    - page (int): page 번호

    Returns:

    - List[schema.Post]: 여러 개의 글 정보가 list 배열에 담겨져 반환
    """
    return post_service.read_posts(db, page)


@router.get(
    "/users/{user_id}/posts",
    response_model=List[schema.Post],
    status_code=status.HTTP_200_OK,
)
def read_user_posts(
    user_id: int,
    page: int,
    post_service: PostService = Depends(),
    db: Session = Depends(db.get_db),
) -> List[schema.Post]:
    """user_id에 일치하는 user가 작성한 글들을 조회한다.
        한 번 조회 시 가져올 글의 갯수는 5개다.

    Args:

     - user_id (int): user의 id
     - page (int): page 번호

    Raises:

    - HTTPException (404 NOT FOUND): user_id에 해당되는 user를 찾지 못한 경우 (code: USER_NOT_FOUND)

    Returns:

     - List[Post]: 여러 글 정보가 list 배열에 담겨져 반환
    """
    return post_service.read_user_posts(db, user_id, page)


@router.post(
    "/users/{user_id}/posts",
    response_model=schema.Post,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    user_id: int,
    data_to_be_created: schema.PostCreate,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """user_id가 현재 로그인된 user와 동일할 때 글을 생성한다.

    Args:

    - user_id (int): 작성자의 id
    - data_to_be_created (PostCreate): 생성할 글의 content 정보
        - content

    Raises:

    - HTTPException (403 FORBIDDEN): 전송된 user_id 값이 로그인된 user의 id와 달라 작성 권한이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 글 생성에 실패한 경우

    Returns:

    - Post: 생성된 post 정보
    """
    return post_service.create_post(
        db,
        user_id,
        current_user.id,
        data_to_be_created.dict(),
    )


@router.patch(
    "/users/{user_id}/posts/{post_id}",
    response_model=schema.Post,
    status_code=status.HTTP_200_OK,
)
def update_post(
    post_id: int,
    data_to_be_updated: schema.PostUpdate,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> schema.Post:
    """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 글을 수정한다.

    Args:

    - post_id (int): 수정될 글의 id
    - data_to_be_updated (PostUpdate): 업데이트할 정보
        - content

    Raises:

    - HTTPException (403 FORBIDDEN): 해당 글의 작성자가 로그인된 user id와 달라 수정 권한이 없는 경우
    - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 글 수정에 실패한 경우

    Returns:

    - Post: 수정된 post 정보
    """
    return post_service.update_post(
        db,
        post_id,
        current_user.id,
        data_to_be_updated.dict(),
    )


@router.delete(
    "/users/{user_id}/posts/{post_id}",
    response_model=Message,
    status_code=status.HTTP_200_OK,
)
def delete_post(
    post_id: int,
    post_service: PostService = Depends(),
    current_user: UserBase = Depends(UserService.get_current_user_verified),
    db: Session = Depends(db.get_db),
) -> Message:
    """현재 로그인된 user가 자신이 작성했고, 해당 post_id에 해당하는 글을 삭제한다.

    Args:

    - user_id (int): 삭제시킬 user의 id
    - post_id (int): 삭제될 글의 id

    Raises:

    - HTTPException (401 UNAUTHORIZED): 글의 작성자가 로그인된 user와 달라 삭제 권한이 없을 경우
    - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
    - HTTPException (500 INTERNAL SERVER ERROR): 글 삭제에 실패한 경우

    Returns:

    - Message: 삭제 성공 메세지를 반환
    """
    post_service.delete_post(
        db,
        post_id,
        current_user.id,
    )
    return {"status": "success", "message": "글이 삭제되었습니다."}
