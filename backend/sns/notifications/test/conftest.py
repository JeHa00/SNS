from typing import Dict

from starlette.background import BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient
from fastapi import status, Request, FastAPI
from sqlalchemy.orm import Session
from redis.client import Redis
import pytest_asyncio
import pytest
import asyncio
import httpx

from sns.common.config import settings

# flake8: noqa
from sns.common.conftest import (
    start_app,
    app,
    db_session,
    redis_db_session,
    client,
    async_client,
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
    fake_post,
    fake_postlike,
    fake_multi_posts,
    fake_multi_post_by_user_logged_in,
)
from sns.posts.service import post_service
from sns.posts.repository import post_crud
from sns.notifications.service import NotificationService
from sns.notifications.repository import RedisQueue
from sns.notifications.schema import NotificationEventData
from sns.notifications.enums import NotificationType


@pytest.fixture(scope="function")
def fake_follow_notifications(
    client: TestClient,
    db_session: Session,
    redis_db_session: Redis,
    get_user_token_headers_and_login_data: Dict,
    fake_multi_user: None,
):
    """
    로그인한 유저 1명과 로그인하지 않은 유저 10명을 생성한다. 로그인하지 않은 유저 10명이 로그인한 유저 1명을 팔로우한다.
    로그인하지 않은 유저 10명은 following이 되고, 로그인한 유저 1명은 follower가 된다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        redis_db_session (Redis): Redis db.
        get_user_token_headers_and_login_data (Dict): 인증 토큰 정보과 로그인 정보를 반환
        fake_multi_user (None): 테스트용 비로그인된 유저 10명을 생성
    """
    follower_email = get_user_token_headers_and_login_data.get("login_data").get(
        "email",
    )

    follower_id = user_crud.get_user(db_session, email=follower_email).id

    first_following_user_id = follower_id + 1

    total_following_user_count = 10

    last_following_user_id = follower_id + total_following_user_count

    for following_id in range(first_following_user_id, last_following_user_id + 1):
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
    get_user_token_headers_and_login_data: Dict,
    fake_multi_post_by_user_logged_in: None,
    fake_user: Dict,
):
    """
    로그인한 유저와 로그인하지 않은 fake_user를 생성한 후, 로그인한 유저가 글 100개를 생성한다.
    그 다음, 생성된 글 100개에 fake_user가 좋아요를 실행한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        redis_db_session (Redis): Redis db.
        fake_multi_post_by_user_logged_in (None): 테스트용으로 로그인한 유저가 생성한 글 100개
        fake_user (Dict): 테스트용으로 로그인하지 않은 유저 1명
    """
    current_user_id = fake_user.get("user").id

    notified_user_email = get_user_token_headers_and_login_data.get("login_data").get(
        "email",
    )

    notified_user_id = user_crud.get_user(
        db_session,
        email=notified_user_email,
    ).id

    total_post_counts = 100

    for post_id in range(1, total_post_counts + 1):
        post_service.like_post(
            db_session,
            redis_db_session,
            BackgroundTasks(),
            post_id,
            current_user_id,
            notified_user_id,
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
            notified_user_id,
        )


@pytest.fixture(scope="function")
def fake_user_logged_in(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
):
    user_logged_in = fake_user.get("user")
    login_data = fake_user.get("login_data")

    user_service.update(db_session, user_logged_in, {"verified": True})

    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return {"headers": headers}


class FakeNotificationService:
    async def send_event(
        self,
        redis_db_session: Redis,
        request: Request,
        current_user_email: str,
    ):
        headers = {
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Origin": "*",
        }

        message_queue = RedisQueue(
            redis_db_session,
            f"notification_useremail:{current_user_email}",
        )

        async def detect_and_send_event():
            while True:
                if (
                    await request.is_disconnected() or message_queue.empty
                ):  #  production 코드와 다른 점
                    break

                if not message_queue.empty:
                    message = message_queue.pop()

                    event_converted_as_string = ""

                    last_event_id = request.headers.get(
                        "lastEventId",
                        message.get("created_at"),
                    )

                    event_type = (
                        NotificationType.follow
                        if message.get("type") == NotificationType.follow
                        else NotificationType.post_like
                    )

                    event = NotificationEventData(
                        event=event_type,
                        id=last_event_id,
                        data=message,
                    ).dict()

                    for key, value in event.items():
                        event_converted_as_string += f"{key}: {value}\n"

                    yield event_converted_as_string + "\n"

                    # 테스트를 위해 시간 1s -> 0.5s로 단축
                    await asyncio.sleep(0.5)

        return StreamingResponse(
            detect_and_send_event(),
            media_type="text/event-stream",
            status_code=status.HTTP_200_OK,
            headers=headers,
        )


@pytest_asyncio.fixture(scope="function")
async def async_client_for_sse(app: FastAPI):
    app.dependency_overrides[NotificationService] = FakeNotificationService

    async with httpx.AsyncClient(
        app=app,
        base_url=f"http://localhost:8000{settings.API_V1_PREFIX}/",
    ) as test_client:
        yield test_client
