from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Post(Base, BaseMixin):
    content = Column(String(1000), nullable=False)
    writer_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    writer = relationship("User", back_populates="posts")

    likee = relationship(
        "PostLike",
        back_populates="liked_post",
        cascade="all, delete-orphan",
    )

    comments = relationship(
        "Comment",
        back_populates="post",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id}, writer_id={self.writer_id})"


class PostLike(Base, BaseMixin):
    user_id_who_like = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    user_who_like = relationship("User", back_populates="liker")

    liked_post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    liked_post = relationship("Post", back_populates="likee")

    is_liked = Column(Boolean, default=True)

    def __repr__(self) -> str:
        return (
            f"PostLike(user_id_who_like={self.user_id_who_like}, "
            f"like_target_id={self.liked_post_id}, "
            f"is_liked={self.is_liked})"
        )
