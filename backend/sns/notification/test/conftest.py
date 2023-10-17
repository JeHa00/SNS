import pytest
import asyncio

from starlette.background import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from redis.client import Redis

# flake8: noqa
from sns.common.conftest import (
    start_app,
    app,
    db_session,
    redis_db_session,
    client,
)

# flake8: noqa
from sns.users.test.conftest import (
    fake_follow,
    fake_user,
    fake_multi_user,
    get_user_token_headers_and_login_data,
)

# flake8: noqa
from sns.users.service import user_service
from sns.users.repositories.db import user_crud
from sns.posts.test.conftest import (
    fake_postlike,
    fake_multi_posts,
    fake_multi_post_by_user_logged_in,
)
from sns.posts.service import post_service
from sns.posts.repository import post_crud


@pytest.fixture(scope="function")
def fake_follow_notifications(
    client: TestClient,
    db_session: Session,
    redis_db_session: Redis,
    get_user_token_headers_and_login_data: dict,
    fake_multi_user: None,
):
    """
    로그인한 유저 1명과 로그인하지 않은 유저 10명을 생성한다. 로그인하지 않은 유저 10명이 로그인한 유저 1명을 팔로우한다.
    로그인하지 않은 유저 10명은 following이 되고, 로그인한 유저 1명은 follower가 된다.
    """
    follower_email = get_user_token_headers_and_login_data.get("login_data").get(
        "email",
    )

    follower_id = user_crud.get_user(db_session, email=follower_email).id

    first_following_user_id = 2

    total_following_user_count = 10

    for following_id in range(first_following_user_id, total_following_user_count + 1):
        user_service.follow_user(
            db_session,
            redis_db_session,
            BackgroundTasks(),
            follower_id,
            following_id,
        )

        new_follow = user_crud.get_follow(
            db_session,
            follower_id,
            following_id,
        )

        user_service.create_and_add_notification(
            db_session,
            redis_db_session,
            new_follow,
        )


@pytest.fixture(scope="function")
def fake_postlike_notifications(
    client: TestClient,
    db_session: Session,
    redis_db_session: Redis,
    fake_multi_post_by_user_logged_in: None,
    fake_user: dict,
):
    """
    로그인한 유저와 로그인하지 않은 fake_user를 생성한 후, 로그인한 유저가 글 100개를 생성한다.
    그 다음, 생성된 글 100개에 fake_user가 좋아요를 실행한다.
    """
    current_user_id = fake_user.get("user").id

    total_post_counts = 100

    for post_id in range(1, total_post_counts + 1):
        post_service.like_post(
            db_session,
            redis_db_session,
            BackgroundTasks(),
            post_id,
            current_user_id,
        )

        new_postlike = post_crud.get_like(
            db_session,
            current_user_id,
            post_id,
        )

        post_service.create_and_add_notification(
            db_session,
            redis_db_session,
            new_postlike,
        )
