from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class User(Base, BaseMixin):
    email = Column(String(50), unique=True)
    password = Column(String(200))
    name = Column(String(20), unique=True)
    profile_text = Column(String(300), nullable=True)
    verified = Column(Boolean, default=False)
    verification_code = Column(String(20), nullable=True, unique=True)

    posts = relationship("Post", back_populates="writer", cascade="all, delete-orphan")
    liker = relationship(
        "PostLike",
        back_populates="user_who_like",
        cascade="all, delete-orphan",
    )

    from_user = relationship(
        "Follow",
        back_populates="following",
        foreign_keys="Follow.following_id",
        cascade="all, delete-orphan",
    )
    to_user = relationship(
        "Follow",
        back_populates="follower",
        foreign_keys="Follow.follower_id",
        cascade="all, delete-orphan",
    )

    comments = relationship(
        "Comment",
        back_populates="writer",
        cascade="all, delete-orphan",
    )

    receiver = relationship(
        "Notification",
        back_populates="notified_user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, name={self.name})"


class Follow(Base, BaseMixin):
    is_followed = Column(Boolean, nullable=False, default=True)

    following_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    following = relationship(
        "User",
        back_populates="from_user",
        foreign_keys=[following_id],
    )

    follower_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    follower = relationship(
        "User",
        back_populates="to_user",
        foreign_keys=[follower_id],
    )

    notification = relationship(
        "Notification",
        back_populates="follow",
        foreign_keys="Notification.follow_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Follow(id={self.id}, "
            f"following_id={self.following_id}, "
            f"follower_id={self.follower_id})"
        )
