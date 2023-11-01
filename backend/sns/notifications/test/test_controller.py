from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
from httpx import AsyncClient
import pytest
import orjson

from sns.common.config import settings
from sns.posts.model import Post


@pytest.mark.mark_as_read
def test_mark_as_read_if_follower_is_not_same_as_current_user(
    client: TestClient,
    db_session: Session,
    fake_follow_notifications: None,
    fake_user_logged_in: dict,
):
    total_fake_follow_data_count = 9

    # token 발행
    headers = fake_user_logged_in.get("headers")

    # 읽음 표시로 변경
    for notification_id in range(1, total_fake_follow_data_count + 1):
        response = client.patch(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers,
        )
        result = response.json()
        result_message = result.get("detail")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert result_message == "수정 권한이 없습니다."


@pytest.mark.mark_as_read
def test_mark_as_read_if_writer_is_not_same_as_current_user(
    client: TestClient,
    db_session: Session,
    fake_postlike_notifications: None,
    fake_user_logged_in: dict,
):
    total_fake_post_like_data_count = 100

    # token 발행
    headers = fake_user_logged_in.get("headers")

    # 읽음 표시로 변경
    for notification_id in range(1, total_fake_post_like_data_count + 1):
        response = client.patch(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers,
        )
        result = response.json()
        result_message = result.get("detail")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert result_message == "수정 권한이 없습니다."


@pytest.mark.mark_as_read
def test_mark_as_read_if_follower_is_same_as_current_user(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: None,
    fake_user_logged_in: dict,
):
    # 로그인한 유저가 fake_user를 팔로우
    headers = get_user_token_headers_and_login_data.get("headers")

    follower_id = 2

    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{follower_id}/follow",
        headers=headers,
    )

    # fake_user 로그인
    headers = fake_user_logged_in.get("headers")

    # 알림 읽기
    notification_id = 1

    response = client.patch(
        f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
        headers=headers,
    )
    result_status_text = response.json().get("status")
    result_message = response.json().get("message")

    assert result_status_text == "success"
    assert result_message == "상태가 읽음 표시로 변경되었습니다."


@pytest.mark.mark_as_read
def test_mark_as_read_if_writer_is_same_as_current_user(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: None,
    fake_user_logged_in: dict,
    fake_post: Post,
):
    # 글 좋아요하기
    headers = get_user_token_headers_and_login_data.get("headers")

    response = client.post(
        f"{settings.API_V1_PREFIX}/posts/{fake_post.id}/like",
        headers=headers,
        json={"writer_id": fake_post.writer_id},
    )

    # fake_user 로그인
    headers = fake_user_logged_in.get("headers")

    # 알림 읽기
    notification_id = 1

    response = client.patch(
        f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
        headers=headers,
    )
    result_status_text = response.json().get("status")
    result_message = response.json().get("message")

    assert result_status_text == "success"
    assert result_message == "상태가 읽음 표시로 변경되었습니다."


@pytest.mark.asyncio
async def test_send_events(
    async_client_for_sse: AsyncClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_follow_notifications: None,
):
    header = get_user_token_headers_and_login_data.get("headers")

    async with async_client_for_sse.stream(
        "GET",
        "notifications",
        headers=header,
    ) as response:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("Cache-Control") == "no-cache"
        assert response.headers.get("Connection") == "keep-alive"
        assert response.headers.get("X-Accel-Buffering") == "no"
        assert (
            response.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
        )
        async for event in response.aiter_raw():
            contents = event.split(b"\n\n")
            contents.pop()  # 빈 문자열 제거
            for content in contents:
                data = content.split(b"\n")

                # event
                assert data[0] == b"event: follow"

                # id
                assert data[1].startswith(b"id:")

                # retry
                assert data[2].startswith(b"retry:")
                length_of_retry_key = len(b"retry:") + 1
                assert data[2][length_of_retry_key:] == str(
                    settings.TIME_TO_RETRY_CONNECTION,
                ).encode("utf-8")

                # data
                assert data[3].startswith(b"data:")
                length_of_data_key = len(b"data:") + 1
                notification_data = (
                    data[3][length_of_data_key:].decode("utf-8").replace("'", '"')
                )
                deserialized_data = orjson.loads(notification_data)
                assert "type" in deserialized_data
                assert deserialized_data["type"] == "follow"
                assert "notification_id" in deserialized_data
                assert type(deserialized_data["notification_id"]) == int
                assert "notified_user_id" in deserialized_data
                assert type(deserialized_data["notified_user_id"]) == int
                assert "following_id" in deserialized_data
                assert type(deserialized_data["following_id"]) == int
                assert "created_at" in deserialized_data
                assert type(deserialized_data["created_at"]) == str
