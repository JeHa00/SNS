from enum import Enum

from pydantic import BaseModel


class NotificationType(str, Enum):
    post = "post"
    like = "like"
    follow = "follow"


class NotificationBase(BaseModel):
    from_user_id: int
    to_user_id: int

    class Config:
        orm_mode = True


class Notification(NotificationBase):
    notification_type: NotificationType
