from typing import Optional
from pydantic import BaseModel, EmailStr, constr


class Token(BaseModel):
    access_token: str
    token_type: str


class UserBase(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

    class Config:
        orm_mode = True


class UserProfileInfo(BaseModel):
    profile_text: Optional[str] = None
    profile_image_name: Optional[str] = None
    profile_image_path: Optional[str] = None
    verified: Optional[str] = None
    verification_code: Optional[str] = None


class UserCreate(UserBase):
    password_confirm: constr(min_length=8)
    verified: bool = False


class UserUpdate(UserProfileInfo):
    password: constr(min_length=8)


class UserRead(UserProfileInfo):
    email: EmailStr
