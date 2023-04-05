from pydantic import BaseModel, Field


class PostBase(BaseModel):
    id: int
    writer_id: int 

    class config:
        orm_mode = True


class PostCreate(BaseModel):
    content: str = Field(max_length=1000)


class PostUpdate(PostCreate):
    pass
     

class Post(PostBase, PostCreate):
    pass 
