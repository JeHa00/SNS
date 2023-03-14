from typing import Optional
from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    email: EmailStr
    password: str


class UserProfileInfo(BaseModel):
    profile_text: Optional[str] = None
    profile_image_name: Optional[str] = None
    profile_image_path: Optional[str] = None


class UserCreate(UserBase):
    password_confirm: str


class UserUpdate(UserProfileInfo):
    password: str


class UserRead(UserProfileInfo):
    email: EmailStr
