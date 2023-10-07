from enum import Enum

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    like = "like"
    follow = "follow"


class NotificationBase(BaseModel):
    class Config:
        orm_mode = True


class Notification(NotificationBase):
    notification_type: NotificationType = Field(title="알림 유형")
    follow_id: int | None
    post_like_id: int | None


class NotificationUpdate(NotificationBase):
    read: bool = True
