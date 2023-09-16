from typing import List, Any
import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from redis.client import Redis

from sns.users.model import User
from sns.posts.model import Post, PostLike


class PostDB:
    def get_post(
        self,
        db: Session,
        post_id: int,
    ) -> Post:
        """post_id에 해당되는 post 정보를 조회한다.

        Args:
            db (Session): db session
            post_id (int): 조회할 post의 id 값

        Returns:
            Post: post_id에 해당되는 Post 객체 정보. 조회 결과 없으면 None을 반환
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        return post

    def get_multi_posts(
        self,
        db: Session,
        writer_id: int,
        skip: int = 0,
        limit: int = 5,
    ) -> List[Post]:
        """writer_id 값에 해당되는 user가 작성한 여러 post들을 조회하여 생성날짜를 기준으로 최신순으로 정렬하여 반환한다.

        Args:
            db (Session): db session
            writer_id (int): writer user의 id
            skip (int, optional): 쿼리 조회 시 건너띌 갯수. 기본 값은 0
            limit (int, optional): 쿼리 조회 시 가져올 최대 갯수. 기본 값은 100

        Returns:
            List[Post]: post 객체 정보들이 list 배열에 담겨져 반환
        """

        query = (
            db.query(Post)
            .filter(Post.writer_id == writer_id)
            .order_by(Post.created_at.desc())
        )
        if skip != 0 or limit != 0:
            query = query.offset(skip).limit(limit)

        return query.all()

    def create(
        self,
        db: Session,
        writer_id: int,
        **post_data: dict,
    ) -> Post:
        """주어진 post_data, writer_id 정보를 가지는 post를 생성한다.

        Args:
            db (Session): db session
            post_data (PostCreate): 생성될 post의 content 정보
            writer_id (int): post를 생성하는 user id

        Returns:
            Post: 생성된 post 정보를 반환
        """
        new_post = Post(
            writer_id=writer_id,
            **post_data,
        )

        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return new_post

    def update(
        self,
        db: Session,
        post: Post,
        **kwargs,
    ) -> Post:
        """post_info에 해당되는 Post 객체를 data_to_be_updated 정보를 가지도록 수정한다.

        Args:
            db (Session): db session
            post_data (Post): 수정할 post 객체 정보로, Post model 또는 id 값으로 전달된다.
            data_to_be_updated (PostUpdate): 수정 시 반영할 내용

        Returns:
            Post: 수정된 post 객체를 반환
        """
        data_to_be_updated = {
            key: value
            for key, value in kwargs.items()
            if hasattr(post, key) and value is not None
        }

        for key, value in data_to_be_updated.items():
            setattr(post, key, value)

        db.add(post)
        db.commit()
        db.refresh(post)

        return post

    def remove(
        self,
        db: Session,
        post_to_be_deleted: Post | int,
    ) -> dict:
        """전달받은 해당 post를 삭제한다.

        Args:
            db (Session): db session
            post_to_be_deleted (Post): 삭제할 post 객체 정보로, Post model 또는 id 값으로 전달된다.

        Returns:
            Dict: 성공 시, 성공 메세지를 반환
        """
        if isinstance(post_to_be_deleted, int):
            post = self.get_post(db, user_id=post_to_be_deleted)
        else:
            post = post_to_be_deleted

        db.delete(post)
        db.commit()

        return {"status": "success"}

    def get_like(
        self,
        db: Session,
        user_id_who_like: int,
        liked_post_id: int,
    ) -> PostLike:
        """주어진 정보에 해당되는 PostLike 객체 정보를 얻는다.

        Args:
            db (Session): db session
            user_id_who_like (int): 좋아요를 한 유저의 id
            liked_post_id (int): 좋아요를 받은 글의 id

        Returns:
            PostLike: 해당 정보에 일치하는 PostLike 객체 정보
        """
        return (
            db.query(PostLike)
            .filter(
                PostLike.liked_post_id == liked_post_id,
                PostLike.user_id_who_like == user_id_who_like,
            )
            .first()
        )

    def get_users_who_like(
        self,
        db: Session,
        liked_post_id: int,
    ) -> List[User]:
        """liked_post_id에 일치하는 글에 좋아요를 한 liker 유저들을 조회한다.

        Args:
            db (Session): db session
            liked_post_id (int): like를 받은 post의 id

        Returns:
            List[User]: list 데이터 타입에 담겨진 User 객체
        """
        subquery = (
            db.query(PostLike)
            .filter(PostLike.liked_post_id == liked_post_id, PostLike.is_liked)
            .order_by(PostLike.updated_at.desc())
            .subquery()
        )

        return (
            db.query(User).join(subquery, User.id == subquery.c.user_id_who_like).all()
        )

    def get_like_targets(
        self,
        db: Session,
        user_id_who_like: int,
    ) -> List[Post]:
        """user_id_who_like 해당하는 user가 좋아요를 한 글들을 조회한다.

        Args:
            db (Session): db session
            user_id_who_like (int): 좋아요를 한 유저의 id

        Returns:
            List[Post]: list 데이터 타입에 담겨진 Post 객체 정보들
        """
        subquery = (
            db.query(PostLike)
            .filter(PostLike.user_id_who_like == user_id_who_like, PostLike.is_liked)
            .order_by(PostLike.updated_at.desc())
            .subquery()
        )

        return db.query(Post).join(subquery, Post.id == subquery.c.liked_post_id).all()

    def like(
        self,
        db: Session,
        user_id_who_like: int,
        liked_post_id: int,
    ) -> PostLike:
        """like_data 를 토대로 post에 좋아요를 실행한다.

        Args:
            db (Session): db session
            user_id_who_like (int): 좋아요를 할 user의 id
            liked_post_id (int): 좋아요를 받을 글의 id

        Returns:
            PostLike: is_liked 값이 True로 생성된 PostLike 객체를 반환
        """
        selected_post_like = self.get_like(
            db,
            user_id_who_like,
            liked_post_id,
        )

        new_like = selected_post_like or PostLike(
            is_liked=True,
            user_id_who_like=user_id_who_like,
            liked_post_id=liked_post_id,
        )

        if not new_like.is_liked:
            new_like.is_liked = True

        db.add(new_like)
        db.commit()
        db.refresh(new_like)

        return new_like

    def unlike(
        self,
        db: Session,
        selected_like: PostLike,
    ) -> PostLike:
        """like_data 를 토대로 post에 좋아요를 취소한다.

        Args:
            db (Session): db session
            selected_like (PostLike): who_like_id, like_target_id, is_liked 값 정보

        Returns:
            PostLike: is_liked 값이 변경된 PostLike 객체를 반환
        """
        selected_like.is_liked = False

        db.add(selected_like)
        db.commit()
        db.refresh(selected_like)

        return selected_like


class PostRedisDB:
    def get_cache(
        self,
        redis_db: Redis,
        key: str,
    ) -> Any:
        """key를 통해 redis에 저장된 value를 얻는다.
        value가 None이면 그대로 반환하고, None이 아니면 역직렬화를 한 후 값을 반환한다.

        Args:
            redis_db (Redis): redis db session
            key (str): redis_db에 저장된 key

        Returns:
            Any: None 이거나 역직렬화를 거친 value
        """
        cache = redis_db.get(key)
        if not cache:
            return cache
        return json.loads(cache)

    def set_cache(
        self,
        redis_db: Redis,
        key: str,
        value: Any,
    ) -> bool:
        """redis_db에 key - value로 저장한다.

        Args:
            redis_db (Redis): redis db session
            key (str): redis_db에 저장된 key
            value (Any): redis_db에 key로 저장된 value

        Returns:
            bool: cache에 저장되면 True
        """
        serialized_value = json.dumps(jsonable_encoder(value))
        redis_db.set(key, serialized_value)
        redis_db.expire(key, 300)

        return True

    def delete_cache(
        self,
        redis_db: Redis,
        key: str,
    ) -> bool:
        """redis_db에 해당 key 값을 삭제한다.

        Args:
            redis_db (Redis): redis db session
            key (str): redis_db에 저장된 key

        Returns:
            bool: 삭제하면 True를 반환
        """
        redis_db.delete(key)
        return True


post_crud = PostDB()
post_redis_crud = PostRedisDB()
