from pydantic import BaseModel, Field

from sns.notification.enums import NotificationType


class NotificationBase(BaseModel):
    class Config:
        orm_mode = True


class Notification(NotificationBase):
    type: NotificationType = Field(title="알림 유형")
    follow_id: int | None
    post_like_id: int | None
