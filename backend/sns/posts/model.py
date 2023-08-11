from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Post(Base, BaseMixin):
    content = Column(String(1000), nullable=False)
    writer_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    writer = relationship("User", back_populates="posts")

    likee = relationship(
        "PostLike",
        back_populates="like_target",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id}, writer_id={self.writer_id})"


class PostLike(Base, BaseMixin):
    who_like_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    who_like = relationship("User", back_populates="liker")

    like_target_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    like_target = relationship("Post", back_populates="likee")

    is_liked = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return (
            f"PostLike(who_like_id={self.who_like_id}, "
            f"like_target_id={self.like_target_id}, "
            f"is_liked={self.is_liked})"
        )
