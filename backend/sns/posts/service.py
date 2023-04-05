from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.posts.model import Post
from sns.posts.schema import PostCreate, PostUpdate


def get_post(db: Session, post_id: int) -> Post:
    post = db.query(Post).filter(Post.id == post_id).first() 
    return post


def get_multi_posts(db: Session, writer_id: int, skip: int = 0, limit: int = 100) -> List[Post]:
    return (db.query(Post).filter(writer_id == writer_id)
            .offset(skip).limit(limit)
            .all()
            )


def create(db: Session, post_info: PostCreate, writer_id: int) -> Post:
    obj_in_data = jsonable_encoder(post_info)
    content = obj_in_data.get("content")
    db_obj = Post(content=content, writer_id=writer_id)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update(db: Session, post_info: Post | int, data_to_be_updated: PostUpdate) -> Post:
    if isinstance(post_info, int):
        post = db.query(Post).filter(Post.id == post_info).first()
    else:
        post = post_info
    obj_data = jsonable_encoder(post)
    if isinstance(data_to_be_updated, dict):
        data_to_be_updated = data_to_be_updated
    else:
        data_to_be_updated = data_to_be_updated.dict(exclude_unset=True)
    for field in obj_data:
        if field in data_to_be_updated:
            setattr(post, field, data_to_be_updated[field])
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def remove(db: Session, post_info: Post | int) -> bool:
    if isinstance(post_info, int):
        post = db.query(Post).filter(Post.id == post_info).first()
    else:
        post = post_info
    db.delete(post)
    db.commit()