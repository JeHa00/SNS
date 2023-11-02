from typing import List

from sqlalchemy.orm import Session

from sns.comments.model import Comment


class CommentDB:
    def get_a_comment(
        self,
        db: Session,
        comment_id: int,
    ) -> Comment:
        """comment_id에 해당되는 comment 객체를 조회한다.

        Args:
            comment_id (int): comment의 id

        Returns:
            Comment: comment_id에 해당되는 comment 객체
        """
        return db.query(Comment).filter(Comment.id == comment_id).one_or_none()

    def get_comments_by_writer_id(
        self,
        db: Session,
        writer_id: int,
        skip: int = 0,
        limit: int = 30,
    ) -> List[Comment]:
        """writer_id에 해당되는 writer가 작성한 comment들을 조회한다.

        Args:
            writer_id (int): user의 id
            skip (int, optional): 건너띌 갯수. 기본 값은 0.
            limit (int, optional): 조회할 최대 갯수. 기본 값은 30.

        Returns:
            List[Comment]: comment 객체들을 list 배열에 담아 반환
        """
        return (
            db.query(Comment)
            .filter(Comment.writer_id == writer_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_comments_by_post_id(
        self,
        db: Session,
        post_id: int,
        skip: int = 0,
        limit: int = 30,
    ) -> List[Comment]:
        """post_id에 해당되는 post에 작성된 comment들을 조회한다.

        Args:
            post_id (int): post의 id
            skip (int, optional): 건너띌 갯수. 기본 값은 0.
            limit (int, optional): 조회할 최대 갯수. 기본 값은 30.

        Returns:
            List[Comment]: comment 객체들을 list 배열에 담아 반환
        """
        return (
            db.query(Comment)
            .filter(Comment.post_id == post_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        db: Session,
        writer_id: int,
        post_id: int,
        content: str,
    ) -> Comment:
        """주어진 정보를 토대로 comment를 생성한다.

        Args:
            writer_id (int): 작성자 유저의 id
            post_id (int): comment가 달릴 post의 id
            content (str): comment의 content로 생성할 내용

        Returns:
            Comment: 생성된 comment 객체를 반환
        """
        new_comment = Comment(
            writer_id=writer_id,
            post_id=post_id,
            content=content,
        )

        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)

        return new_comment

    def update(
        self,
        db: Session,
        comment: Comment,
        **kwargs,
    ) -> Comment:
        """Comment 모델 객체 또는 comment_id 로 주어진 comment 객체를
           data_to_be_updated로 받은 내용으로 수정한다.

        Args:
            comment_data (Comment | int): Comment 객체 정보
            kwargs: 수정에 반영될 내용

        Returns:
            Comment: 수정된 Comment 객체를 반환
        """
        data_to_be_updated = {
            key: value
            for key, value in kwargs.items()
            if hasattr(comment, key) and value is not None
        }

        for key, value in data_to_be_updated.items():
            setattr(comment, key, value)

        db.add(comment)
        db.commit()
        db.refresh(comment)

        return comment

    def delete(self, db: Session, comment_to_be_deleted: Comment | int):
        """Comment 모델 객체 또는 comment_id 로 주어진 comment 객체를 삭제한다.

        Args:
            comment_to_be_deleted (Comment | int): 삭제될 Comment 객체 정보
        """
        if isinstance(comment_to_be_deleted, int):
            comment = (
                db.query(Comment).filter(Comment.id == comment_to_be_deleted).first()
            )
        else:
            comment = comment_to_be_deleted

        db.delete(comment)
        db.commit()

        return {"status": "success"}


comment_crud = CommentDB()
