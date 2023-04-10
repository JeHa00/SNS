from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from sns.comments.model import Comment
from sns.comments.schema import CommentCreate, CommentUpdate


class CommentDB:
    def get_comment(self, db: Session, comment_id: int) -> Comment:
        """comment_id에 해당되는 comment 객체를 조회한다.

        Args:
            comment_id (int): comment의 id

        Returns:
            Comment: comment_id에 해당되는 comment 객체
        """
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        return comment

    def get_multi_comments(
        self, db: Session, skip: int = 0, limit: int = 100, **kwargs
    ) -> List[Comment]:
        """writer_id에 해당되는 writer가 작성한 comment들, 또는 post_id에 해당되는 post에 작성된 comment들을 조회한다.

        Args:
            skip (int, optional): 건너띌 갯수. 기본 값은 0.
            limit (int, optional): 조회할 최대 갯수. 기본 값은 100.
            kwargs: writer_id 또는 post_id를 key = value로 입력

        Returns:
            List[Comment]: comment 객체들을 list 배열에 담아 반환
        """
        if kwargs["writer_id"]:
            return (
                db.query(Comment)
                .filter(Comment.writer_id == kwargs["writer_id"])
                .offset(skip)
                .limit(limit)
                .all()
            )
        elif kwargs["post_id"]:
            return (
                db.query(Comment)
                .filter(Comment.post_id == kwargs["post_id"])
                .offset(skip)
                .limit(limit)
                .all()
            )

    def create(
        self,
        db: Session,
        data_to_be_created: CommentCreate,
        writer_id: int,
        post_id: int,
    ) -> Comment:
        """주어진 정보를 토대로 comment를 생성한다.

        Args:
            data_to_be_created (CommentCreate): comment의 content로 생성할 내용
            writer_id (int): 작성자 유저의 id
            post_id (int): comment가 달릴 post의 id

        Returns:
            Comment: 생성된 comment 객체를 반환
        """
        obj_in_data = jsonable_encoder(data_to_be_created)
        content = obj_in_data.get("content")

        db_obj = Comment(content=content, writer_id=writer_id, post_id=post_id)

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def update(
        self,
        db: Session,
        comment_info: Comment | int,
        data_to_be_updated: CommentUpdate,
    ) -> Comment:
        """Comment 모델 객체 또는 comment_id 로 주어진 comment 객체를 data_to_be_updated로 받은 내용으로 수정한다.

        Args:
            comment_info (Comment | int): Comment 객체 정보
            data_to_be_updated (CommentUpdate): 수정에 반영될 내용

        Returns:
            Comment: 수정된 Comment 객체를 반환
        """
        if isinstance(comment_info, int):
            post = db.query(Comment).filter(Comment.id == comment_info).first()
        else:
            post = comment_info

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

    def remove(self, db: Session, comment_info: Comment | int):
        """Comment 모델 객체 또는 comment_id 로 주어진 comment 객체를 삭제한다.

        Args:
            comment_info (Comment | int): Comment 객체 정보
        """
        if isinstance(comment_info, int):
            comment = db.query(Comment).filter(Comment.id == comment_info).first()
        else:
            comment = comment_info

        db.delete(comment)
        db.commit()


comment_crud = CommentDB()
