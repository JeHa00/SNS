from sqlalchemy import Column, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin
from sns.notifications.enums import NotificationType


class Notification(Base, BaseMixin):
    type = Column(Enum(NotificationType))

    follow_id = Column(Integer, ForeignKey("follow.id", ondelete="CASCADE"), index=True)
    follow = relationship(
        "Follow",
        back_populates="notification",
        foreign_keys=[follow_id],
    )

    post_like_id = Column(
        Integer,
        ForeignKey("postlike.id", ondelete="CASCADE"),
        index=True,
    )
    post_like = relationship(
        "PostLike",
        back_populates="notification",
        foreign_keys=[post_like_id],
    )

    notified_user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        index=True,
    )
    notified_user = relationship(
        "User",
        back_populates="receiver",
        foreign_keys=[notified_user_id],
    )

    read = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"Notification(id={self.id}, type={self.type}, read={self.read})"
