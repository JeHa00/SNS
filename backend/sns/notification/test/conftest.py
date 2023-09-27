import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, redis_db_session, client

# flake8: noqa
from sns.users.test.conftest import (
    fake_follow,
    fake_user,
    fake_multi_user,
    get_user_token_headers_and_login_data,
)

# flake8: noqa
from sns.posts.test.conftest import fake_postlike, fake_multi_posts
from sns.notification.repository import notification_crud


@pytest.fixture(scope="function")
def fake_multi_follow_notification(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
):
    total_fake_follow_data_count = 64
    for follow_id in range(1, total_fake_follow_data_count + 1):
        notification_crud.create_notification_on_follow(
            db_session,
            follow_id=follow_id,
        )


@pytest.fixture(scope="function")
def fake_multi_postlike_notification(
    client: TestClient,
    db_session: Session,
    fake_postlike: None,
):
    total_fake_post_like_data_count = 150
    for post_like_id in range(1, total_fake_post_like_data_count + 1):
        notification_crud.create_notification_on_postlike(
            db_session,
            post_like_id=post_like_id,
        )
