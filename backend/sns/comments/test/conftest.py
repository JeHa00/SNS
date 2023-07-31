import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import app, client, db_session, start_app

# flake8: noqa
from sns.users.test.conftest import fake_user, get_user_token_headers_and_login_data

from sns.users.test.utils import random_lower_string

# flake8: noqa
from sns.posts.test.conftest import fake_post

from sns.users.service import user_service
from sns.posts.model import Post
from sns.comments.repository import comment_crud
from sns.comments.schema import CommentCreate
from sns.comments.model import Comment


@pytest.fixture(scope="function")
def fake_comment(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
) -> Comment:
    # writer 정보
    writer = fake_user.get("user")

    # verified 업데이트
    user_service.update(db_session, writer, {"verified": True})

    # content 정보
    content = CommentCreate(
        content=random_lower_string(k=500),
        writer_id=writer.id,
        post_id=fake_post.id,
    )

    # comment 생성
    comment = comment_crud.create(
        db_session,
        writer.id,
        fake_post.id,
        **content.dict(),
    )

    return comment


@pytest.fixture(scope="function")
def fake_multi_comments(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
    fake_post: Post,
) -> None:
    # writer 정보
    writer = fake_user.get("user")

    # 생성할 comment 총 수
    total_comment_count_to_produce = 100

    # comment 생성
    while total_comment_count_to_produce > 0:
        content = CommentCreate(
            content=random_lower_string(k=500),
            writer_id=writer.id,
            post_id=fake_post.id,
        )
        comment_crud.create(
            db_session,
            writer.id,
            fake_post.id,
            **content.dict(),
        )
        total_comment_count_to_produce -= 1
