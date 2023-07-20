from sqlalchemy import Column, String, Boolean

from sns.common.base import Base, BaseMixin


class User(Base, BaseMixin):
    email = Column(String(50), unique=True)
    password = Column(String(200), nullable=False)
    name = Column(String(20), unique=True)
    profile_text = Column(String(300), nullable=True)
    profile_image_name = Column(String(50), nullable=True)
    profile_image_path = Column(String(200), nullable=True)
    verified = Column(Boolean, default=False)
    verification_code = Column(String(20), nullable=True, unique=True)

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, name={self.name})"
