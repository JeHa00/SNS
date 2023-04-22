from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class User(Base, BaseMixin):
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    name = Column(String(20), nullable=False, unique=True)
    profile_text = Column(String(300), nullable=True)
    profile_image_name = Column(String(50), nullable=True)
    profile_image_path = Column(String(200), nullable=True)
    verified = Column(Boolean, default=False)
    verification_code = Column(String(20), nullable=True, unique=True)
    posts = relationship("Post", back_populates="writer", cascade="all, delete-orphan")
    from_user = relationship(
        "Follow", back_populates="follower", cascade="all, delete-orphan"
    )
    to_user = relationship(
        "Follow", back_populates="following", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, name={self.name})"


class Follow(Base, BaseMixin):
    following_id = Column(Integer, ForeignKey("user.id"), ondelete="CASCADE")
    following = relationship("User", back_populates="from_user")

    follower_id = Column(Integer, ForeignKey("user.id"), ondelete="CASCADE")
    follower = relationship("User", back_populates="to_user")

    is_followed = Column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return (
            f"Follow(id={self.id}, "
            f"following_id={self.following_id}, "
            f"follower_id={self.follower_id})"
        )
