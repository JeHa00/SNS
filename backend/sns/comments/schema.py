from pydantic import BaseModel, Field
from datetime import datetime


class CommentBase(BaseModel):
    content: str | None = Field(max_length=500)

    class Config:
        orm_mode = True


class CommentInDB(CommentBase):
    id: int
    writer_id: int
    post_id: int
    created_at: datetime
    updated_at: datetime


class Comment(CommentInDB):
    content: str = Field(max_length=500)


class CommentCreate(CommentBase):
    content: str = Field(max_length=500)


class CommentUpdate(CommentCreate):
    pass
