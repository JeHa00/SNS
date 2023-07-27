from pydantic import BaseModel, EmailStr, Field, validator


class Msg(BaseModel):
    status: str
    msg: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: str


class UserBase(BaseModel):
    email: EmailStr

    class Config:
        orm_mode = True


class UserCreate(UserBase):
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


class UserRead(UserBase):
    email: EmailStr | None
    name: str
    profile_text: str | None


class UserUpdate(BaseModel):
    verified: bool = False
    profile_text: str | None


class UserPasswordUpdate(BaseModel):
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
