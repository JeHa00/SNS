from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Comment(Base, BaseMixin):
    content = Column(String(500), nullable=False)
    writer_id = Column(Integer, ForeignKey("user.id"))
    post_id = Column(Integer, ForeignKey("post.id"))
    writer = relationship("User", back_populates='comments')
    post = relationship("Post", back_populates="comments")