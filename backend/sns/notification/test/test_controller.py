from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

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
