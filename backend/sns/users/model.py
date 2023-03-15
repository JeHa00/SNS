from sqlalchemy import Column, String, Boolean

from sns.common.base import Base, BaseMixin


class User(Base, BaseMixin):
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    profile_text = Column(String(300), nullable=True)
    profile_image_name = Column(String(50), nullable=True)
    profile_image_path = Column(String(200), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    verification_code = Column(String(10), nullable=True, unique=True)
