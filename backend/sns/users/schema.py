from pydantic import BaseModel, EmailStr, Field


class Msg(BaseModel):
    status: str
    msg: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str


class UserBase(BaseModel):
    email: EmailStr | None
    password: str | None = Field(min_length=8)
    verified: bool = False

    class Config:
        orm_mode = True


class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)
    verified: bool = False


class UserRead(UserBase):
    name: str
    profile_text: str | None = None


class UserUpdate(BaseModel):
    verified: bool | None = False
    profile_text: str | None = None


class UserPasswordUpdate(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
