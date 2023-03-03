from sqlalchemy import Column, String 
from sqlalchmey.orm import relationship 

from sns.common.session import Base
from sns.common.base import BaseMixin

class User(Base, BaseMixin):
    login_name = Column(String(10), nullable=False, unique=True)
    email = Column(String(50), nullable=False, unique=True)
    password = Column(String(200), nullable=False)
    profile_text = Column(String(300), nullable=True)
    profile_image_name = Column(String(50), nullable=True)
    profile_image_path = Column(String(200), nullable=True)