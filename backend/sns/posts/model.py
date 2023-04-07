from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from sns.common.base import Base, BaseMixin


class Post(Base, BaseMixin):
    content = Column(String(1000), nullable=False)
    writer_id = Column(Integer, ForeignKey("user.id"))
    writer = relationship("User", back_populates="posts")

    def __repr__(self) -> str:
        return f"Post(id={self.id}, writer_id={self.writer_id}, created_at={self.created_at})"
    