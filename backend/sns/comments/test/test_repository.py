from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.test.utils import random_lower_string
from sns.users.service import user_service
from sns.posts.service import post_service
from sns.posts.model import Post
from sns.comments.repository import comment_crud
from sns.comments.model import Comment
from sns.comments import schema


def test_create(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
):
    # 유저 정보
    user = fake_user.get("user")

    # 댓글 내용
    data_to_be_created = schema.CommentCreate(
        content=random_lower_string(k=500),
    )

    # 생성한 댓글
    comment = comment_crud.create(
        db_session,
        writer_id=user.id,
        post_id=fake_post.id,
        content=data_to_be_created.content,
    )

    assert comment is not None
    assert hasattr(comment, "id")
    assert comment.id == 1
    assert hasattr(comment, "content")
    assert len(comment.content) == 500
    assert hasattr(comment, "writer_id")
    assert comment.writer_id == user.id
    assert hasattr(comment, "post_id")
    assert comment.post_id == fake_post.id
    assert hasattr(comment, "writer")
    assert comment.writer == user
    assert hasattr(comment, "post")
    assert comment.post == fake_post
    assert hasattr(comment, "created_at")
    assert hasattr(comment, "updated_at")


def test_get_a_comment(client: TestClient, db_session: Session, fake_comment: Comment):
    # 댓글 정보
    comment = comment_crud.get_a_comment(db_session, fake_comment.id)

    assert comment is not None


def test_get_comments_by_writer_id(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
    fake_multi_comments: None,
):
    # 유저 정보
    user = fake_user.get("user")

    # 생성한 댓글들
    comments = comment_crud.get_comments_by_writer_id(
        db_session,
        user.id,
    )

    assert comments is not None
    assert len(comments) == 30

    for comment in comments:
        assert hasattr(comment, "id")
        assert hasattr(comment, "content")
        assert len(comment.content) == 500
        assert hasattr(comment, "writer_id")
        assert comment.writer_id == user.id
        assert hasattr(comment, "post_id")
        assert comment.post_id == fake_post.id
        assert hasattr(comment, "writer")
        assert comment.writer == user
        assert hasattr(comment, "post")
        assert comment.post == fake_post
        assert hasattr(comment, "created_at")
        assert hasattr(comment, "updated_at")


def test_get_comments_by_post_id(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
    fake_multi_comments: None,
):
    # 유저 정보
    user = fake_user.get("user")

    # 생성한 댓글들
    comments = comment_crud.get_comments_by_post_id(db_session, fake_post.id, None)

    assert comments is not None
    assert len(comments) == 30

    for comment in comments:
        assert hasattr(comment, "id")
        assert hasattr(comment, "content")
        assert len(comment.content) == 500
        assert hasattr(comment, "writer_id")
        assert comment.writer_id == user.id
        assert hasattr(comment, "post_id")
        assert comment.post_id == fake_post.id
        assert hasattr(comment, "writer")
        assert comment.writer == user
        assert hasattr(comment, "post")
        assert comment.post == fake_post
        assert hasattr(comment, "created_at")
        assert hasattr(comment, "updated_at")


def test_update_only_one(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
):
    new_content = random_lower_string(k=500)
    data_to_be_updated = schema.CommentUpdate(content=new_content)
    comment = comment_crud.update(
        db_session,
        fake_comment,
        **data_to_be_updated.dict(),
    )
    assert comment is not None
    assert comment.id == fake_comment.id
    assert comment.content == new_content


def test_update_multi_comments(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    old_content = fake_post.content
    new_content = random_lower_string(k=500)
    data_to_be_updated = schema.CommentUpdate(content=new_content)
    comments = comment_crud.get_comments_by_post_id(db_session, fake_post.id, None)

    assert len(comments) == 30

    for comment_model_object in comments:
        comment = comment_crud.update(
            db_session,
            comment_model_object,
            **data_to_be_updated.dict(),
        )
        assert comment.content != old_content
        assert comment.content == new_content


def test_remove_only_one_by_int(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
):
    comment_id = fake_comment.id
    comment_crud.delete(
        db_session,
        comment_id,
    )
    comment = comment_crud.get_a_comment(
        db_session,
        comment_id,
    )

    assert comment is None


def test_remove_only_one_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_comment: Comment,
):
    comment_crud.delete(
        db_session,
        fake_comment,
    )
    comment = comment_crud.get_a_comment(
        db_session,
        fake_comment.id,
    )

    assert comment is None


def test_remove_comments_by_int(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_comments_by_post_id(
        db_session,
        fake_post.id,
        None,
    )

    assert len(comments) == 30

    for comment in comments:
        comment_crud.delete(
            db_session,
            comment.id,
        )
        comment = comment_crud.get_a_comment(
            db_session,
            comment.id,
        )

        assert comment is None


def test_remove_comments_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_comments_by_post_id(
        db_session,
        fake_post.id,
    )

    assert len(comments) == 30

    for comment in comments:
        comment_crud.delete(
            db_session,
            comment,
        )
        comment = comment_crud.get_a_comment(
            db_session,
            comment.id,
        )

        assert comment is None


def test_remove_comments_by_deleting_user(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_comments: None,
):
    user = fake_user.get("user")
    comments = comment_crud.get_comments_by_writer_id(
        db_session,
        user.id,
    )

    assert len(comments) == 30

    user_service.remove(db_session, user)
    comments = comment_crud.get_comments_by_writer_id(
        db_session,
        user.id,
    )

    assert len(comments) == 0


def test_remove_comments_by_deleting_post(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_comments_by_post_id(
        db_session,
        fake_post.id,
        None,
    )

    assert len(comments) == 30

    post_service.remove(
        db_session,
        fake_post,
    )
    comments = comment_crud.get_comments_by_post_id(
        db_session,
        fake_post.id,
        None,
    )

    assert len(comments) == 0
