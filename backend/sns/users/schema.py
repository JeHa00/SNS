from pydantic import BaseModel, EmailStr, Field, validator


class Message(BaseModel):
    status: str
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str


class Base(BaseModel):
    class Config:
        orm_mode = True


class UserCreate(Base):
    email: EmailStr
    password: str = Field(min_length=8)
    password_confirm: str = Field(min_length=8)

    @validator("password_confirm")
    def passwords_match(
        cls,
        value,
        values,
    ):
        if "password" in values and value != values["password"]:
            raise ValueError("두 비밀번호가 일치하지 않습니다.")
        return value


class UserPasswordUpdate(Base):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)

    @validator("new_password")
    def passwords_update_match(
        cls,
        value,
        values,
    ):
        if "current_password" in values and value == values["current_password"]:
            raise ValueError("새로 입력한 패스워드가 기존 패스워드와 동일합니다.")
        return value


class UserBase(Base):
    id: int
    email: EmailStr


class UserPrivateRead(UserBase):
    name: str
    profile_text: str | None


class UserRead(Base):
    id: int
    name: str
    profile_text: str | None


class UserReadWithFollowed(UserRead):
    followed: bool


class UserUpdate(Base):
    name: str | None
    profile_text: str | None
