from pydantic import BaseModel, Field
from datetime import datetime


class PostBase(BaseModel):
    content: str | None = Field(max_length=1000)

    class Config:
        orm_mode = True


class PostInDB(PostBase):
    id: int
    writer_id: int
    created_at: datetime
    updated_at: datetime


class PostCreate(BaseModel):
    content: str = Field(max_length=1000)


class PostUpdate(PostCreate):
    pass


class Post(PostInDB):
    content: str = Field(max_length=1000)


class PostLikeInDB(BaseModel):
    is_like: bool = True

    class Config:
        orm_mode = True


class PostLike(PostLikeInDB):
    who_like_id: int | None
    like_target_id: int | None


class PostUnlike(PostLike):
    is_like: bool = False
