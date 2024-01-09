from pydantic import BaseModel, Field
from datetime import datetime

from sns.common.config import settings
from sns.notifications.enums import NotificationType


class NotificationBase(BaseModel):
    class Config:
        orm_mode = True


class NotificationBaseData(NotificationBase):
    type: NotificationType
    notified_user_id: int
    read: bool
    created_at: datetime


class FollowNotificationData(NotificationBaseData):
    notification_id: int
    following_id: int
    read: bool = Field(default=False)


class PostLikeNotificationData(NotificationBaseData):
    notification_id: int
    user_id_who_like: int
    liked_post_id: int
    read: bool = Field(default=False)


class NotificationData(NotificationBaseData):
    id: int
    user_id_who_like: int | None
    liked_post_id: int | None
    following_id: int | None


class NotificationEventData(NotificationBase):
    event: NotificationType
    id: str
    retry: int = settings.TIME_TO_RETRY_CONNECTION
    data: dict
