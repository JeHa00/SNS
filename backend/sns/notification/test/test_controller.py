from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

from sns.common.config import settings
from sns.users.service import user_service


@pytest.mark.mark_as_read
def test_mark_as_read_if_follower_is_not_same_as_current_user(
    client: TestClient,
    db_session: Session,
    fake_follow_notifications: None,
    fake_user: dict,
):
    total_fake_follow_data_count = 9

    # token 발행
    user_logged_in = fake_user.get("user")
    login_data = fake_user.get("login_data")

    user_service.update(db_session, user_logged_in, {"verified": True})

    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
    fake_user: dict,
):
    total_fake_post_like_data_count = 100

    # token 발행
    user_logged_in = fake_user.get("user")
    login_data = fake_user.get("login_data")

    user_service.update(db_session, user_logged_in, {"verified": True})

    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

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
