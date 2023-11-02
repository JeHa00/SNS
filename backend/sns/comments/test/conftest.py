import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import app, client, db_session, start_app, redis_db_session

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
    """테스트용 댓글 데이터 1개를 생성한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        fake_user (dict): 테스트용으로 비로그인, 이메일 미인증 유저 1명을 생성
        fake_post (Post): 테스트용 글 데이터 1개를 생성. fake_user가 작성한 글이다.

    Returns:
        Comment: fake_post에 달린 댓글 정보를 반환
    """
    # writer 정보
    writer = fake_user.get("user")

    # verified 업데이트
    user_service.update(db_session, writer, {"verified": True})

    # content 정보
    content = CommentCreate(content=random_lower_string(k=500))

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
    """테스트용 댓글 데이터 100개를 생성

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        fake_user (dict): 테스트용으로 비로그인, 이메일 미인증 유저 1명을 생성
        fake_post (Post): 테스트용 글 데이터 1개를 생성. fake_user가 작성한 글이다.
    """
    # writer 정보
    writer = fake_user.get("user")

    # 생성할 comment 총 수
    total_comment_count_to_produce = 100

    # comment 생성
    while total_comment_count_to_produce > 0:
        content = CommentCreate(content=random_lower_string(k=500))
        comment_crud.create(
            db_session,
            writer.id,
            fake_post.id,
            **content.dict(),
        )
        total_comment_count_to_produce -= 1
