from typing import List

from starlette.background import BackgroundTasks
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.users.repositories.db import user_crud
from sns.users.model import User
from sns.posts.repository import post_crud, post_redis_crud
from sns.posts.model import Post, PostLike


class PostService:
    POST_NOT_FOUND_ERROR = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="주어진 정보에 일치하는 글을 찾을 수 없습니다.",
    )

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
            raise self.POST_NOT_FOUND_ERROR

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
            raise self.POST_NOT_FOUND_ERROR

        return post

    def read_posts(
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
                - writer_id에 해당되는 user를 찾지 못한 경우
                - writer_id에 해당되는 user가 작성한 글이 없는 경우
                - 해당 page에 작성된 글이 없는 경우

        Returns:
            - List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """
        post_size_per_page = 5

        # user 유무 확인
        selected_user = user_crud.get_user(
            db,
            user_id=writer_id,
        )

        if not selected_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "USER_NOT_FOUND",
                    "message": "해당되는 유저를 찾을 수 없습니다.",
                },
            )

        # post 조회
        posts = post_crud.get_multi_posts(
            db,
            writer_id,
            skip=page * post_size_per_page,
            limit=limit,
        )

        if len(posts) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "POST_NOT_FOUND",
                    "message": "주어진 정보에 일치하는 글을 찾을 수 없습니다.",
                },
            )
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
            - data_to_be_created (PostCreate): 생성할 post의 content 정보
            - current_user_id (int): 현재 로그인된 유저의 id

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

            - user_id (int): 수정할 user의 id
            - post_id (int): 수정될 post의 id
            - data_to_be_updated (PostUpdate): 업데이트할 정보
            - current_user_id (int): 현재 로그인된 유저의 id

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

            - user_id (int): 삭제시킬 user의 id
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

    def get_like(
        self,
        db: Session,
        user_id_who_like: int,
        liked_post_id: int,
    ) -> PostLike | None:
        """입력받은 정보를 PostLikeDB class에 전달하여 post_like_data를 가지고 있는 PostLike 모델 객체를 조회한다.
            없으면 None을 반환한다.

        Args:
            - db (Session): db session.
            - user_id_who_like (int): 좋아요를 한 유저의 id
            - liked_post_id (int): 좋아요를 받은 글의 id

        Returns:
            - PostLike: 조회된 PostLike 객체를 반환
            - 없으면 None을 반환
        """
        return post_crud.get_like(
            db,
            user_id_who_like,
            liked_post_id,
        )

    def read_likers(
        self,
        db: Session,
        redis_db: Redis,
        liked_post_id: int,
        background_tasks: BackgroundTasks,
    ) -> List[User]:
        """입력받은 정보를 PostLikeDB class에 전달하여 주어진 post id에 해당하는 post를 좋아요한 user들을 조회한다.

        Args:
            - db (Session): db session.
            - redis_db (Redis): Redis db
            - liked_post_id (int): 좋아요를 받은 post의 id

        Raises:
            - HTTPException(404 NOT FOUND): 다음 2가지 경우에 발생한다.
                - like_target_id에 해당하는 post를 조회하지 못한 경우
                - 해당 post에 좋아요를 한 user들이 없으면 발생

        Returns:
            - List[User]: 해당 post에 좋아요를 유저들을 반환
        """
        selected_post = post_crud.get_post(
            db,
            liked_post_id,
        )

        if not selected_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "POST_NOT_FOUND",
                    "message": "주어진 정보에 일치하는 글을 찾을 수 없습니다.",
                },
            )

        cache = post_redis_crud.get_cache(redis_db, f"post::{liked_post_id}")

        if cache is None:
            users = post_crud.get_users_who_like(db, liked_post_id)

            if len(users) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "LIKER_NOT_FOUND",
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

    def read_likees(
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
        posts = post_crud.get_like_targets(db, current_user_id)

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
        post_id: int,
        current_user_id: int,
    ) -> PostLike:
        """입력받은 정보를 PostLikeDB class에 전달하여 해당되는 PostLike 객체가 존재하지 않으면 새로 생성한다.
           하지만, 객체는 존재하지만 is_liked 정보가 False이면 True로 수정한다.

        Args:
            - db (Session): db session
            - like_data (dict): 이미 존재하거나 새로 생성할 PostLike 객체 정보

        Raises:
            - HTTPException (400 BAD REQUEST): 이미 is_liked 상태 값이 True인 경우
            - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): post 좋아요 작업에 실패한 경우

        Returns:
            - PostLike: 새로 생성되거나 변경된 PostLike 객체를 반환
        """
        self.get_post_and_handle_none(db, post_id)

        try:
            post_crud.like(
                db,
                current_user_id,
                post_id,
            )
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="post 좋아요에 실패했습니다.",
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
            - unlike_data (dict): PostLike 객체 정보

        Raises:
            - HTTPException (400 BAD REQUEST): 이미 is_liked 상태 값이 False이면 발생
            - HTTPException (404 NOT FOUND): post_id에 해당하는 글이 없는 경우
            - HTTPException (500 INTERNAL SERVER ERROR): post 좋아요 취소 작업에 실패하면 발생

        Returns:
            - bool: 취소 작업을 완료하면 True를 반환
        """
        self.get_post_and_handle_none(db, post_id)

        post_like_object = self.get_like(
            db,
            current_user_id,
            post_id,
        )

        if post_like_object and not post_like_object.is_liked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 좋아요가 취소되었습니다.",
            )

        try:
            post_crud.unlike(db, post_like_object)
            return True
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="post 좋아요 취소에 실패했습니다.",
            )


post_service = PostService()
