import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import app, client, db_session, start_app
from sns.common.config import settings

# flake8: noqa
from sns.users.test.conftest import fake_user, get_user_token_headers_and_user_info
from sns.users.test.utils import random_lower_string
from sns.users.schema import UserUpdate
from sns.users.service import update, get_user
from sns.posts.test.conftest import fake_post
from sns.posts.model import Post
from sns.comments.repository import comment_crud
from sns.comments.schema import CommentCreate
from sns.comments.model import Comment


@pytest.fixture(scope="function")
def fake_comment(
    client: TestClient, db_session: Session, fake_user: dict, fake_post: Post
) -> Comment:
    # writer 정보
    writer = fake_user.get("user")

    # content 정보
    content = CommentCreate(
        content=random_lower_string(k=500), writer_id=writer.id, post_id=fake_post.id
    )

    # comment 생성
    comment = comment_crud.create(
        db_session,
        data_to_be_created=content,
        writer_id=writer.id,
        post_id=fake_post.id,
    )

    return comment


@pytest.fixture(scope="function")
def fake_multi_comments(
    client: TestClient, db_session: Session, fake_user: dict, fake_post: Post
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
            data_to_be_created=content,
            writer_id=writer.id,
            post_id=fake_post.id,
        )
        total_comment_count_to_produce -= 1


@pytest.fixture(scope="function")
def fake_user_headers_and_info(
    client: TestClient, db_session: Session, fake_user: dict
):
    # 유저 정보
    user_info = fake_user.get("user_info")  # 유저 이메일 및 해쉬 전 비밀번호 정보
    user = get_user(db_session, email=user_info.email)
    # BUG: get_user가 아닌 fake_user.get("user") 로 User 정보를 가져올 경우 jsonable_encoder가 빈 객체를 반환.

    # verified 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, user, info_to_be_updated)

    # 로그인
    login_info = {"email": user_info.email, "password": user_info.password}
    response = client.post(f"{settings.API_V1_STR}/login", json=login_info)

    # headers 반환
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "user_info": login_info}
