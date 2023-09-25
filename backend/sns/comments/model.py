from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin

# flake8: noqa
from sns.users.model import User

# flake8: noqa
from sns.posts.model import Post


class Comment(Base, BaseMixin):
    content = Column(String(500), nullable=False)

    writer_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    writer = relationship("User", back_populates="comments")

    post_id = Column(Integer, ForeignKey("post.id", ondelete="CASCADE"))
    post = relationship("Post", back_populates="comments")

    def __repr__(self) -> str:
        return (
            f"Comment(id={self.id}, writer_id={self.writer_id}, post_id={self.post_id})"
        )
