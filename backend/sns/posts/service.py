from typing import List

from starlette.background import BackgroundTasks
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.common.http_exceptions import CommonHTTPExceptions
from sns.users.repositories.db import user_crud
from sns.users.model import User
from sns.posts.repository import post_crud, post_redis_crud
from sns.posts.model import Post, PostLike
from sns.notifications.repository import notification_crud, RedisQueue
from sns.notifications.schema import PostLikeNotificationData


class PostService:
    POSTS_PER_A_PAGE = 5

    def get_post_and_handle_none(
        self,
        db: Session,
        post_id: int,
    ) -> Post:
        """post_id 값을 가지고 있는 user를 조회한다. none일 경우 에러를 발생시킨다.

        Args:
            - post_id (int): 조회할 post의 id

        Raises:
            - HTTPException (404 NOT FOUND): post_id 에 해당되는 post를 찾지 못할 경우

        Returns:
            - Post : 조회된 post를 반환
        """

        selected_post = post_crud.get_post(
            db,
            post_id,
        )

        if not selected_post:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return selected_post

    def create(
        self,
        db: Session,
        writer_id: int,
        post_data: dict,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 해당 정보를 가지는 post를 생성한다.

        Args:
            - writer_id (int): post를 생성하는 user id
            - post_data (dict): 생성될 post의 content 정보

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): post 생성에 실패했을 때 발생

        Returns:
            - Post: 생성된 post 정보를 반환
        """
        try:
            created_post = post_crud.create(
                db,
                writer_id,
                **post_data,
            )
            return created_post
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 생성에 실패하였습니다.",
            )

    def update(
        self,
        db: Session,
        post_data: Post,
        data_to_be_updated: dict,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여
           post_data에 해당되는 Post 객체에 data_to_be_updated 정보로 수정한다.

        Args:
            - post_data (Post): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            - data_to_be_updated (dict): 수정 시 반영할 내용

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): post 수정 실패 시 발생

        Returns:
            - Post: 수정된 post 객체를 반환
        """
        try:
            updated_post = post_crud.update(
                db,
                post_data,
                **data_to_be_updated,
            )
            return updated_post
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 수정에 실패하였습니다.",
            )

    def remove(
        self,
        db: Session,
        post_to_be_deleted: Post,
    ) -> bool:
        """입력받은 정보를 PostDB class에 전달하여 post_to_be_deleted 해당되는 post 객체를 삭제한다.

        Args:
            - post_to_be_deleted (Post): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): post 삭제에 실패했을 때 발생

        Returns:
            - bool: post 삭제에 성공하면 True를 반환
        """
        try:
            post_crud.remove(
                db,
                post_to_be_deleted,
            )
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="글 삭제에 실패하였습니다.",
            )

    def read_post(
        self,
        db: Session,
        post_id: int,
    ) -> Post:
        """입력받은 정보를 PostDB class에 전달하여 post_id에 해당하는 Post 정보를 조회한다.

        Args:
            - post_id (int): 읽어올 post의 id

        Raises:
            - HTTPException(404 NOT FOUND): post_id에 해당되는 post를 찾을 수 없을 때 발생

        Returns:
            - Post: post_id에 해당되는 post 반환
        """
        post = post_crud.get_post(
            db,
            post_id,
        )
        if not post:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return post

    def read_posts(
        self,
        db: Session,
        page: int,
    ) -> List[Post]:
        """전체 글 목록을 조회한다.

        Args:
            page (int): 페이지 번호

        Raises:
            - HTTPException(404 NOT FOUND): 작성된 글이 없는 경우 (code: POST_NOT_FOUND)

        Returns:
            - List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """
        posts = post_crud.get_posts(
            db,
            skip=page * self.POSTS_PER_A_PAGE,
        )

        if not posts:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return posts

    def read_posts_of_followers(
        self,
        db: Session,
        current_user_id: int,
        page: int = 0,
    ) -> List[Post]:
        """현재 로그인한 유저의 팔로워 유저들이 작성한 글들을 조회한다.
           작성된 글들은 생성 날짜를 기준으로 정렬되어 받는다.

        Args:

        - current_user_id (int): 현재 로그인한 유저의 id
        - page (int): 조회할 page 번호.

        Raises:

        - HTTPException (404 NOT FOUND): 다음 경우에 대해서 발생한다.
            - 팔로우 유저가 없는 경우
            - 팔로우 유저가 작성한 글이 없는 경우 (code: POST_NOT_FOUND)
            - 해당 page에 글이 없는 경우 (code: POST_NOT_FOUND)

        Returns:

        -  List[Post]: 조회된 글들의 목록
        """

        followers = user_crud.get_followers(db, current_user_id)

        if not followers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="팔로우한 유저가 없습니다.",
            )

        posts = post_crud.get_posts_of_followers(
            db,
            current_user_id,
            skip=page * self.POSTS_PER_A_PAGE,
        )

        if not posts:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return posts

    def read_posts_of_a_user(
        self,
        db: Session,
        writer_id: int,
        page: int,
        limit: int = 5,
    ) -> List[Post]:
        """입력받은 정보를 PostDB class에 전달하여 writer_id 값에 해당되는 user가 작성한 여러 post들을 조회한다.

        Args:
            - writer_id (int): writer user의 id
            - skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            - limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 5

        Raises:
            - HTTPException(404 NOT FOUND): 다음 경우에 발생
                - writer_id에 해당되는 user를 찾지 못한 경우 (code: USER_NOT_FOUND)
                - writer_id에 해당되는 user가 작성한 글이 없는 경우 (code: POST_NOT_FOUND)
                - 해당 page에 작성된 글이 없는 경우 (code: POST_NOT_FOUND)

        Returns:
            - List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """

        # user 유무 확인
        selected_user = user_crud.get_user(
            db,
            user_id=writer_id,
        )

        if not selected_user:
            raise CommonHTTPExceptions.USER_NOT_FOUND_ERROR

        # post 조회
        posts = post_crud.get_posts_of_a_user(
            db,
            writer_id,
            skip=page * self.POSTS_PER_A_PAGE,
            limit=limit,
        )

        if len(posts) == 0:
            raise CommonHTTPExceptions.POST_NOT_FOUND_ERROR

        return posts

    def create_post(
        self,
        db: Session,
        writer_id: int,
        current_user_id: int,
        data_to_be_created: dict,
    ) -> Post:
        """user_id가 current_user와 동일할 때 post를 생성한다.

        Args:
            - writer_id (int): 글을 작성할 user의 id
            - current_user_id (int): 현재 로그인된 유저의 id
            - data_to_be_created (PostCreate): 생성할 post의 content 정보

        Raises:
            - HTTPException (403 FORBIDDEN): writer_id가 로그인된 user id와 달라 작성 권한이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): post 생성에 실패한 경우

        Returns:
              - Post: 생성된 post 정보 반환
        """
        if writer_id == current_user_id:
            post = self.create(
                db,
                writer_id,
                data_to_be_created,
            )
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="작성 권한이 없습니다.",
            )

    def update_post(
        self,
        db: Session,
        post_id: int,
        current_user_id: int,
        data_to_be_updated: dict,
    ) -> Post:
        """user_id가 현재 user id와 동일하여 수정 권한이 있을 때 post_id에 해당되는 post를 수정한다.

        Args:
            - post_id (int): 수정될 post의 id
            - current_user_id (int): 현재 로그인된 유저의 id
            - data_to_be_updated (PostUpdate): 업데이트할 정보

        Raises:
            - HTTPException (403 FORBIDDEN): 해당 글의 작성자가 로그인된 user id와 달라 수정 권한이 없는 경우
            - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): post 정보 변경에 실패한 경우

        Returns:
             - Post: 수정된 post 객체 반환
        """
        post = self.get_post_and_handle_none(db, post_id)

        if post.writer_id == current_user_id:
            self.update(
                db,
                post,
                data_to_be_updated,
            )
            return post
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="수정 권한이 없습니다.",
            )

    def delete_post(
        self,
        db: Session,
        post_id: int,
        current_user_id: int,
    ) -> None:
        """user_id가 current_user의 id와 동일할 때, 해당 post_id를 가진 post를 삭제한다.

        Args:
            - db (Session): db session
            - post_id (int): 삭제될 post의 id
            - current_user_id (int): 현재 로그인된 유저의 id

        Raises:
            - HTTPException (403 FORBIDDEN): 글의 작성자와 로그인된 user id와 달라 삭제 권한이 없는 경우
            - HTTPException (404 NOT FOUND): writer_id에 해당되는 user가 작성한 글이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): post 삭제에 실패한 경우
        """
        post = self.get_post_and_handle_none(db, post_id)

        if post.writer_id == current_user_id:
            self.remove(
                db,
                post_to_be_deleted=post,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="삭제 권한이 없습니다.",
            )

    def read_users_who_like(
        self,
        db: Session,
        redis_db: Redis,
        liked_post_id: int,
        background_tasks: BackgroundTasks,
    ) -> List[User]:
        """입력받은 정보를 PostLikeDB class에 전달하여 주어진 post id에 해당하는 post를 좋아요한 user들을 조회한다.

        Args:
            - db (Session): db session
            - redis_db (Redis): Redis db
            - liked_post_id (int): 좋아요를 받은 post의 id
            - background_tasks (BackgroundTasks): background 작업 수행을 위해 필요

        Raises:
            - HTTPException(404 NOT FOUND): 다음 2가지 경우에 발생한다.
                - liked_post_id에 해당하는 post를 조회하지 못한 경우 (code: POST_NOT_FOUND)
                - 해당 post에 좋아요를 한 user들이 없으면 발생 (code: USER_WHO_LIKE_NOT_FOUND)

        Returns:
            - List[User]: 해당 post에 좋아요를 유저들을 반환
        """
        self.get_post_and_handle_none(db, liked_post_id)

        cache = post_redis_crud.get_cache(redis_db, f"post::{liked_post_id}")

        if cache is None:
            users = post_crud.get_users_who_like(db, liked_post_id)

            if len(users) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "USER_WHO_LIKE_NOT_FOUND",
                        "message": "해당 글에 좋아요를 한 유저가 없습니다.",
                    },
                )

            data = {
                "redis_db": redis_db,
                "key": f"post::{liked_post_id}",
                "value": users,
            }

            background_tasks.add_task(
                post_redis_crud.set_cache,
                **data,
            )

            return users

        return cache

    def read_liked_posts(
        self,
        db: Session,
        current_user_id: int,
    ) -> List[Post]:
        """current_user_id에 해당하는 user가 좋아요를 한 post들을 조회한다.

        Args:
            - db (Session): db session
            - current_user_id (int): user의 id

        Raises:
            - HTTPException(404 NOT FOUND): 해당 유저가 좋아요를 한 글이 없는 경우

        Returns:
            - List[Post]: 좋아요를 받은 post들을 반환
        """
        posts = post_crud.get_liked_posts(db, current_user_id)

        if len(posts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 유저가 좋아요를 한 글이 없습니다.",
            )
        else:
            return posts

    def like_post(
        self,
        db: Session,
        redis_db: Redis,
        background_tasks: BackgroundTasks,
        post_id: int,
        current_user_id: int,
    ) -> bool:
        """입력받은 정보를 PostLikeDB class에 전달하여 해당되는 PostLike 객체가 존재하지 않으면 새로 생성한다.
           하지만, 객체는 존재하지만 is_liked 정보가 False이면 True로 수정한다.

        Args:
            - db (Session): db session
            - redis_db (Redis): Redis db
            - background_tasks (BackgroundTasks): background task를 위한 객체
            - post_id (int): 좋아요를 받는 글의 id
            - current_user_id (int): 좋아요를 하는 현재 로그인한 유저 id

        Raises:
            - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): 다음 2가지 경우에 발생
                - 글 좋아요에 실패한 경우 (code: FAILED_TO_LIKE_POST)
                - 알림 생성에 실패한 경우 (code: FAILED_TO_CREATE_NOTIFICATION)

        Returns:
            - bool: 좋아요 성공 시 True, 실패 시 에러를 발생
        """
        liked_post = self.get_post_and_handle_none(db, post_id)

        try:
            postlike = post_crud.like(
                db,
                current_user_id,
                post_id,
            )

            background_tasks.add_task(
                self.create_and_add_notification,
                db,
                redis_db,
                postlike,
                liked_post.writer_id,
            )

            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FAILED_TO_LIKE_POST",
                    "detail": "post 좋아요에 실패했습니다.",
                },
            )

    def unlike_post(
        self,
        db: Session,
        post_id: int,
        current_user_id: int,
    ) -> bool:
        """입력받은 정보를 PostLikeDB class에 전달하여 is_liked를 False로 상태 변경하여 좋아요를 취소한다.

        Args:
            - db (Session): db session
            - post_id (int): 좋아요를 받은 post의 id
            - current_user_id (int): 현재 로그인한 user의 id

        Raises:
            - HTTPException (404 NOT FOUND): 다음 2가지 경우에 발생한다.
                - post_id에 해당하는 글이 없는 경우 (code: POST_NOT_FOUND)
                - 주어진 정보에 해당하는 PostLike 정보가 없는 경우 (code: POST_LIKE_NOT_FOUND)
            - HTTPException (500 INTERNAL SERVER ERROR): post 좋아요 취소 작업에 실패하면 발생

        Returns:
            - bool: 취소 작업을 완료하면 True를 반환
        """
        selected_post = post_crud.get_post(
            db,
            post_id,
        )

        if not selected_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "POST_NOT_FOUND",
                    "message": "주어진 정보에 일치하는 글을 찾을 수 없습니다.",
                },
            )

        post_like_object = post_crud.get_like(
            db,
            current_user_id,
            post_id,
        )

        if not post_like_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "POST_LIKE_NOT_FOUND",
                    "message": "해당 정보에 일치하는 좋아요 정보를 찾을 수 없습니다.",
                },
            )

        try:
            post_crud.unlike(db, post_like_object)
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="post 좋아요 취소에 실패했습니다.",
            )

    def create_and_add_notification(
        self,
        db: Session,
        redis_db: Redis,
        new_post_like: PostLike,
        notified_user_id: int,
    ) -> bool:
        """주어진 데이터를 가지고 알림을 생성하고, message queue에 추가한다.
        writer_id를 통해서 writer의 email 정보를 얻은 후, 이 정보를 queue의 key값으로 사용하여 queue를 생성한다.
        그리고 이 queue에 bytestr 타입으로 post_like event data를 추가한다.

        Args:
            - db (Session): mysql db session
            - redis_db (Redis): message queue에 접속하는 db
            - message_queue (RedisQueue): redis_db를 통해 생성되는 message_queue
            - new_post_like (PostLike): 새로 생성된 PostLike 객체
            - notified_user_id (int): 알림 수신 유저의 id

        Raises:
            - HTTPException (500 INTERNAL SERVER ERROR): 알림 생성에 실패한 경우
                - code: FAILED_TO_CREATE_NOTIFICATION

        Returns:
            - bool : 성공 시 True를 반환
        """
        try:
            new_notification = notification_crud.create_notification_on_postlike(
                db,
                new_post_like.id,
                notified_user_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FAILED_TO_CREATE_NOTIFICATION",
                    "detail": "알림 생성에 실패했습니다.",
                },
            )

        notification_data = PostLikeNotificationData(
            type=new_notification.type,
            notification_id=new_notification.id,
            notified_user_id=notified_user_id,
            user_id_who_like=new_post_like.user_id_who_like,
            liked_post_id=new_post_like.liked_post_id,
            created_at=str(new_post_like.created_at),
        )

        # message_queue 초기화 및 알림 데이터 추가
        message_queue = RedisQueue(
            redis_db,
            f"notification_useremail:{new_notification.notified_user.email}",
        )
        message_queue.push(notification_data.dict())

        return True


post_service = PostService()
