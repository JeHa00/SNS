from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from sns.users.service import delete as user_remove
from sns.users.test.utils import random_lower_string
from sns.posts.model import Post
from sns.posts.service import remove as post_remove
from sns.comments.model import Comment
from sns.comments.repository import comment_crud
from sns.comments.schema import CommentCreate, CommentUpdate


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
    new_content = random_lower_string(k=500)
    data_to_be_updated = CommentUpdate(content=new_content)
    comment = comment_crud.update(
        db_session, comment_info=fake_comment.id, data_to_be_updated=data_to_be_updated
    )
    assert comment is not None
    assert comment.id == fake_comment.id
    assert comment.content == new_content


def test_update_only_one_by_model_object(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    new_content = random_lower_string(k=500)
    data_to_be_updated = CommentUpdate(content=new_content)
    comment = comment_crud.update(
        db_session, comment_info=fake_comment, data_to_be_updated=data_to_be_updated
    )
    assert comment is not None
    assert comment.id == fake_comment.id
    assert comment.content == new_content


def test_update_multi_comments_by_int(
    client: TestClient,
    db_session: Session,
    fake_multi_comments: None,
):
    new_content = random_lower_string(k=500)
    content = CommentUpdate(content=new_content)

    for comment_id in range(1, 101):
        comment = comment_crud.update(
            db_session, comment_info=comment_id, data_to_be_updated=content
        )
        assert comment is not None
        assert comment.content == new_content


# NOTE: Post domain에서 발생한 것과 동일한 문제
def test_update_multi_comments_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    old_content = fake_post.content
    new_content = random_lower_string(k=500)
    content = CommentUpdate(content=new_content)
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert len(comments) == 100

    for comment_model_object in comments:
        assert hasattr(comment_model_object, "content")  # NOTE: 이게 없으면 FAILED 발생
        comment = comment_crud.update(
            db_session, comment_info=comment_model_object, data_to_be_updated=content
        )
        assert comment.content != old_content
        assert comment.content == new_content


def test_remove_only_one_by_int(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    comment_id = fake_comment.id
    comment_crud.remove(db_session, comment_info=comment_id)
    comment = comment_crud.get_comment(db_session, comment_id=comment_id)

    assert comment is None


def test_remove_only_one_by_model_object(
    client: TestClient, db_session: Session, fake_comment: Comment
):
    comment_crud.remove(db_session, comment_info=fake_comment)
    comment = comment_crud.get_comment(db_session, comment_id=fake_comment.id)

    assert comment is None


def test_remove_multi_comments_by_int(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert len(comments) == 100

    for comment in comments:
        comment_crud.remove(db_session, comment_info=comment.id)
        comment = comment_crud.get_comment(db_session, comment_id=comment.id)

        assert comment is None


def test_remove_multi_comments_by_model_object(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert len(comments) == 100

    for comment in comments:
        comment_crud.remove(db_session, comment_info=comment)
        comment = comment_crud.get_comment(db_session, comment_id=comment.id)

        assert comment is None


def test_remove_multi_comments_by_deleting_user(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_multi_comments: None,
):
    user = fake_user.get("user")
    comments = comment_crud.get_multi_comments(db_session, writer_id=user.id)

    assert len(comments) == 100

    user_remove(db_session, user_info=user)
    comments = comment_crud.get_multi_comments(db_session, writer_id=user.id)

    assert len(comments) == 0


def test_remove_multi_comments_by_deleting_post(
    client: TestClient,
    db_session: Session,
    fake_post: Post,
    fake_multi_comments: None,
):
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert len(comments) == 100

    post_remove(db_session, post_info=fake_post)
    comments = comment_crud.get_multi_comments(db_session, post_id=fake_post.id)

    assert len(comments) == 0
