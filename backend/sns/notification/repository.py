from sqlalchemy.orm import Session

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
    ) -> Notification:
        """새로 생성된 follow 객체에 대해 notification 객체를 생성한다.

        Args:
            db (Session): db session
            follow_id (int): follow 객체의 id

        Returns:
            Notification: 생성된 notification 객체
        """
        new_notification = Notification(
            follow_id=follow_id,
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
    ) -> Notification:
        """새로 생성된 postlike 객체에 대해 notification 객체를 생성한다.

        Args:
            db (Session): db session
            post_like_id (int): postlike 객체의 id

        Returns:
            Notification: 생성된 notification 객체
        """
        new_notification = Notification(
            post_like_id=post_like_id,
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


notification_crud = NotificationDB()
