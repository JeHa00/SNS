from sqlalchemy import Column, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Notification(Base, BaseMixin):
    from_user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    from_user = relationship(
        "User", back_populates="sender", foreign_keys=[from_user_id]
    )

    to_user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    to_user = relationship("User", back_populates="receiver", foreign_keys=[to_user_id])

    notification_type = Column(Enum("post", "follow", "like"), nullable=False)

    related_post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    related_post = relationship(
        "Post",
        back_populates="post_used_in_notification",
        foreign_keys=[related_post_id],
    )

    def __repr__(self) -> str:
        return (
            f"Notification(notification_type={self.notification_type}, "
            f"from_user_id={self.from_user_id}, "
            f"to_user_id={self.to_user_id})"
        )
