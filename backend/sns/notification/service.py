from fastapi import status, HTTPException
from sqlalchemy.orm import Session

from sns.users.repositories.db import user_crud
from sns.posts.repository import post_crud
from sns.notification.repository import notification_crud


class NotificationService:
    def change_is_read_state_to_true(
        self,
        db: Session,
        notification_id: int,
        current_user_id: int,
    ) -> bool:
        """알림의 읽기 상태를 읽음 상태로 변경한다.

        Args:
            db (Session): db session
            notification_id (int): Notification의 id

        Raises:
            HTTPException (403 FORBIDDEN): 수정 권한이 없는 경우
            HTTPException (500 INTERNAL SERVER ERROR): 알림 읽기 상태 변경에 실패한 경우

        Returns:
            bool: 성공 시 True
        """
        selected_notification = notification_crud.get_notification_by_id(
            db,
            notification_id,
        )

        if selected_notification.notification_type == "follow":
            selected_follow = user_crud.get_a_follow_by_follow_id(
                db,
                selected_notification.follow_id,
            )
            if selected_follow.follower_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="수정 권한이 없습니다.",
                )

        else:
            selected_postlike = post_crud.get_like_by_postlike_id(
                db,
                selected_notification.id,
            )

            selected_post = post_crud.get_post(
                db,
                selected_postlike.like_target_id,
            )

            if selected_post.writer_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="수정 권한이 없습니다.",
                )

        try:
            notification_crud.change_is_read_state(
                db,
                notification_id,
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 읽기 상태 변경에 실패했습니다.",
            )

        return True


notification_service = NotificationService()
