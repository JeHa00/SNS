from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin
from sns.comments.model import Comment


class Post(Base, BaseMixin):
    content = Column(String(1000), nullable=False)
    writer_id = Column(Integer, ForeignKey("user.id"))
    comment_id = Column(Integer, ForeignKey("comment.id"))
    writer = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")