from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status
import pytest

from sns.common.config import settings
from sns.users.service import user_service


@pytest.mark.change_is_read_state_to_true
def test_change_is_read_if_follower_is_not_same_as_current_user(
    client: TestClient,
    fake_multi_follow_notification: None,
    get_user_token_headers_and_login_data: dict,
):
    total_fake_follow_data_count = 64
    headers = get_user_token_headers_and_login_data.get("headers")

    for notification_id in range(1, total_fake_follow_data_count + 1):
        response = client.patch(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers,
            json={"is_read": True},
        )
        result = response.json()
        result_message = result.get("detail")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert result_message == "수정 권한이 없습니다."


@pytest.mark.change_is_read_state_to_true
def test_change_is_read_if_writer_is_not_same_as_current_user(
    client: TestClient,
    get_user_token_headers_and_login_data: dict,
    fake_multi_postlike_notification: None,
):
    total_fake_post_like_data_count = 150
    headers = get_user_token_headers_and_login_data.get("headers")

    for notification_id in range(1, total_fake_post_like_data_count + 1):
        response = client.patch(
            f"{settings.API_V1_PREFIX}/notifications/{notification_id}",
            headers=headers,
            json={"is_read": True},
        )
        result = response.json()
        result_message = result.get("detail")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert result_message == "수정 권한이 없습니다."


@pytest.mark.change_is_read_state_to_true
def test_change_is_read_if_follower_is_same_as_current_user(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_user: dict,
):
    # following 유저로 로그인하기
    headers = get_user_token_headers_and_login_data.get("headers")

    # follow 관계 맺기 그리고, 알림 객체 생성하기
    follower = fake_user.get("user")
    response = client.post(
        f"{settings.API_V1_PREFIX}/users/{follower.id}/follow",
        headers=headers,
    )

    new_notification_id = 1

    # follower 유저로 로그인하기
    login_data = fake_user.get("login_data")
    user_service.update(db_session, follower, {"verified": True})  # follower 이메일 인증하기

    login_data = {
        "email": login_data.get("email"),
        "password": login_data.get("password"),
    }
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # follower의 알림을 읽음 상태로 변경하기
    response = client.patch(
        f"{settings.API_V1_PREFIX}/notifications/{new_notification_id}",
        headers=headers,
        json={"is_read": True},
    )
    result = response.json()
    result_status = result.get("status")
    result_message = result.get("message")

    assert response.status_code == status.HTTP_200_OK
    assert result_status == "success"
    assert result_message == "상태가 읽음 표시로 변경되었습니다."
