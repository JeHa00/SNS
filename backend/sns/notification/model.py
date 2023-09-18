from sqlalchemy import Column, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Notification(Base, BaseMixin):
    notification_type = Column(Enum("follow", "post_like"))

    follow_id = Column(Integer, ForeignKey("follow.id", ondelete="CASCADE"))
    follow = relationship(
        "Follow",
        back_populates="notification",
        foreign_keys=[follow_id],
    )

    post_like_id = Column(Integer, ForeignKey("postlike.id", ondelete="CASCADE"))
    post_like = relationship(
        "PostLike",
        back_populates="notification",
        foreign_keys=[post_like_id],
    )

    is_read = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"Notification(type={self.notification_type}, is_read={self.is_read})"
