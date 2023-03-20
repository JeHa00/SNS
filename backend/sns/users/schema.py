from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class Msg(BaseModel):
    status: str
    msg: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class UserBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    verified: bool = False

    class Config:
        orm_mode = True


class UserProfile(BaseModel):
    name: str
    profile_text: Optional[str] = None


class UserCreate(UserBase):
    password_confirm: str = Field(min_length=8)
    verified: bool = False


class UserUpdate(UserProfile):
    password: str = Field(min_length=8)


class UserRead(UserProfile, UserBase):
    pass
