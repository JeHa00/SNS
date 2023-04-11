from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.test.utils import random_lower_string
from sns.posts.model import Post
from sns.comments.model import Comment
from sns.comments.repository import comment_crud
from sns.comments.schema import CommentCreate


def test_create(
    client: TestClient, db_session: Session, fake_user: dict, fake_post: Post
):
    # 유저 정보
    user = fake_user.get("user")

    # 댓글 내용
    data_to_be_created = CommentCreate(
        content=random_lower_string(k=500), writer_id=user.id, post_id=fake_post.id
    )

    # 생성한 댓글
    comment = comment_crud.create(
        db_session,
        data_to_be_created=data_to_be_created,
        writer_id=user.id,
        post_id=fake_post.id,
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


def test_get_comment(client: TestClient, db_session: Session, fake_comment: Comment):
    # 댓글 정보
    comment = comment_crud.get_comment(db_session, comment_id=fake_comment.id)

    assert comment is not None
    assert comment.id == 1


def test_get_multi_comments_by_writer_id(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
    fake_multi_comments: None,
):
    # 유저 정보
    user = fake_user.get("user")

    # 생성한 댓글들
    comments = comment_crud.get_multi_comments(db_session, writer_id=user.id)

    assert comments is not None
    assert len(comments) == 100

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


def test_get_multi_comments_by_post_id(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
    fake_multi_comments: None,
):
    # 유저 정보
    user = fake_user.get("user")

    # 생성한 댓글들
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert comments is not None
    assert len(comments) == 100

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


def test_update_only_one_by_int(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    pass


def test_update_only_one_by_model_object(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    pass


def test_update_multi_comments_by_int(
    client: TestClient,
    db_session: Session,
    fake_multi_comments: None,
):
    pass


def test_update_multi_comments_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_multi_comments: None,
):
    pass


def test_remove_only_one_by_int(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    pass


def test_remove_only_one_by_model_object(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    pass


def test_remove_multi_comments_by_int(
    client: TestClient,
    db_session: Session,
    fake_multi_comments: None,
):
    pass


def test_remove_multi_comments_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_multi_comments: None,
):
    pass
