from pydantic import BaseModel, Field

from sns.common.config import settings
from sns.notification.enums import NotificationType


class NotificationBase(BaseModel):
    class Config:
        orm_mode = True


class Notification(NotificationBase):
    type: NotificationType = Field(title="알림 유형")
    follow_id: int | None
    post_like_id: int | None


class NotificationBaseData(NotificationBase):
    type: NotificationType
    notification_id: int
    notified_user_id: int
    created_at: str


class FollowNotificationData(NotificationBaseData):
    following_id: int


class PostLikeNotificationData(NotificationBaseData):
    user_id_who_like: int
    liked_post_id: int


class NotificationEventData(NotificationBase):
    event: NotificationType
    id: str
    retry: int = settings.TIME_TO_RETRY_CONNECTION
    data: dict
