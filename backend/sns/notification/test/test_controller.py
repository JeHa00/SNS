from fastapi.testclient import TestClient
from fastapi import status
import pytest

from sns.common.config import settings


@pytest.mark.mark_as_read
def test_mark_as_read_if_follower_is_not_same_as_current_user(
    client: TestClient,
    fake_follow_notifications: None,
    get_user_token_headers_and_login_data: dict,
):
    total_fake_follow_data_count = 64
    headers = get_user_token_headers_and_login_data.get("headers")

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
    get_user_token_headers_and_login_data: dict,
    fake_postlike_notifications: None,
):
    total_fake_post_like_data_count = 150
    headers = get_user_token_headers_and_login_data.get("headers")

    for notification_id in range(1, total_fake_post_like_data_count + 1):
        response = client.patch(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers,
        )
        result = response.json()
        result_message = result.get("detail")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert result_message == "수정 권한이 없습니다."
