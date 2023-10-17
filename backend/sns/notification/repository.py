from typing import Dict, Any
import orjson

from sqlalchemy.orm import Session
from redis.client import Redis

from sns.notification.model import Notification
from sns.notification.enums import NotificationType


class NotificationDB:
    def get_notification_by_id(
        self,
        db: Session,
        notification_id: int,
    ) -> Notification:
        """notification_id에 해당하는 Notification 객체를 조회한다.

        Args:
            db (Session): db session
            notification_id (int): 조회할 Notification의 follow_id 속성 값

        Returns:
            Notification: 조회된 Notification 객체. 해당되는 객체가 없으면 None을 반환
        """
        return db.query(Notification).get(notification_id)

    def get_notification_by_follow_id(
        self,
        db: Session,
        follow_id: int,
    ) -> Notification:
        """주어진 follow_id에 일치하는 notification을 조회한다.

        Args:
            db (Session): db session
            follow_id (int): 조회할 Notification의 follow_id 속성 값

        Returns:
            Notification: 조회된 Notification 객체. 해당되는 객체가 없으면 None을 반환
        """
        return (
            db.query(Notification)
            .filter(Notification.follow_id == follow_id)
            .one_or_none()
        )

    def get_notification_by_postlike_id(
        self,
        db: Session,
        post_like_id: int,
    ) -> Notification:
        """주어진 post_like_id에 일치하는 notification을 조회한다.

        Args:
            db (Session): db session
            post_like_id (int): 조회할 Notification의 post_like_id 속성 값

        Returns:
            Notification: 조회된 Notification 객체. 해당되는 객체가 없으면 None을 반환
        """
        return (
            db.query(Notification)
            .filter(Notification.post_like_id == post_like_id)
            .one_or_none()
        )

    def create_notification_on_follow(
        self,
        db: Session,
        follow_id: int,
        notified_user_id: int,
    ) -> Notification:
        """새로 생성된 follow 객체에 대해 notification 객체를 생성한다.

        Args:
            db (Session): db session
            follow_id (int): follow 객체의 id
            notified_user_id (int): 알림을 수신하는 유저의 id

        Returns:
            Notification: 생성된 notification 객체
        """
        new_notification = Notification(
            follow_id=follow_id,
            notified_user_id=notified_user_id,
            type=NotificationType.follow,
        )

        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        return new_notification

    def create_notification_on_postlike(
        self,
        db: Session,
        post_like_id: int,
        notified_user_id: int,
    ) -> Notification:
        """새로 생성된 postlike 객체에 대해 notification 객체를 생성한다.

        Args:
            db (Session): db session
            post_like_id (int): postlike 객체의 id
            notified_user_id (int): 알림을 수신하는 유저의 id

        Returns:
            Notification: 생성된 notification 객체
        """
        new_notification = Notification(
            post_like_id=post_like_id,
            notified_user_id=notified_user_id,
            type=NotificationType.post_like,
        )

        db.add(new_notification)
        db.commit()
        db.refresh(new_notification)

        return new_notification

    def mark_as_read(
        self,
        db: Session,
        notification_id: int,
    ) -> Notification:
        """notification_id에 해당하는 Notification 객체의 is_read 상태를 True로 변경한다.

        Args:
            db (Session): db session
            notification_id (int): Notification의 id

        Returns:
            Notification: 수정된 Notification 객체
        """
        selected_notification = self.get_notification_by_id(db, notification_id)
        selected_notification.read = True

        db.add(selected_notification)
        db.commit()
        db.refresh(selected_notification)

        return selected_notification


class RedisQueue:
    def __init__(
        self,
        db: Redis,
        key: str,
    ):
        """redis_queue를 주어진 정보로 초기화하여 인스턴스를 생성한다.

        Args:
            key (str): queue의 key 값
            db (Redis): redis의 db connection
        """
        self.redis_db = db
        self.key = key

    @property
    def size(self) -> int:
        """redis_queue의 전체 크기 값을 반환한다.

        Returns:
            int: redis_queue의 전체 크기 값 반환
        """
        return self.redis_db.llen(self.key)

    @property
    def empty(self) -> bool:
        """redis_queue가 빈 값인지 확인한다.

        Returns:
            bool: 빈 값 유무 값 반환
        """
        return self.size == 0

    def exists(self) -> bool:
        """self.key가 redis db에 존재하는지 판단하여, 있으면 True 없으면 False를 반환
        없으면 value와 함께 queue에 추가해야한다.

        Returns:
            bool: key가 존재하면 True, 없으면 False를 반환
        """
        return bool(self.redis_db.exists(self.key))

    def push(self, element) -> bool:
        """입력한 element를 redis_queue에 추가한다.

        Args:
            element: model 객체 정보를 받는다.

        Returns:
            bool: 추가 성공 시 True, 실패는 False를 반환
        """
        return bool(self.redis_db.lpush(self.key, element))

    def pop(self) -> Dict[str, Any] | None:
        """맨 마지막 인덱스에 해당하는 값을 얻고, 삭제한다.
           하지만, 빈 값인 경우 None을 반환한다.

        Returns:
            byte | None: 맨 마지막 인덱스 값 또는 None
        """
        return orjson.loads(self.redis_db.rpop(self.key)) if not self.empty else None

    def read(self) -> Dict[str, Any] | None:
        """맨 마지막 인덱스에 해당하는 값을 단지 읽는다. 제거하지 않는다.

        Returns:
            Dict: 맨 마지막 값
        """
        return (
            orjson.loads(self.redis_db.lindex(self.key, -1)) if not self.empty else None
        )

    def clear(self) -> bool:
        """해당 queue를 삭제한다. 성공하면 True, 실패하면 False를 반환한다.

        Returns:
            bool: 성공하면 True, 실패하면 False를 반환
        """
        return bool(self.redis_db.delete(self.key))


notification_crud = NotificationDB()
