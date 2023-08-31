from random import randint
from typing import Dict
import pytest
import secrets

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from fastapi import status

from sns.common.config import settings
from sns.users.schema import UserUpdate, UserPasswordUpdate
from sns.users.test.utils import random_email, random_lower_string
from sns.users.service import user_service


@pytest.mark.signup
def test_signup_if_email_is_not_verified(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
):
    # fake_user 정보
    login_data = fake_user["login_data"]

    # 회원가입 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/signup",
        json=login_data,
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_message == "인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요."


@pytest.mark.signup
def test_signup_if_email_is_already_verified(
    fake_user: dict,
    client: TestClient,
    db_session: Session,
):
    # fake_user 정보
    user = fake_user["user"]
    signup_data = fake_user["login_data"]

    # verified 정보 업데이트
    user_service.update(db_session, user, {"verified": True})

    # 회원가입 및 결과
    response = client.post(f"{settings.API_V1_PREFIX}/signup", json=signup_data)
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_message == "이미 인증된 이메일입니다."


@pytest.mark.verify_email
def test_verify_email_if_code_is_not_registered(client: TestClient):
    code = secrets.token_urlsafe(10)  # 등록되지 않은 인증 코드 생성

    # 이메일 인증 및 결과
    response = client.post(f"{settings.API_V1_PREFIX}/verification-email/{code}")
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND

    # code가 등록되지 않았다는 건 아직 회원가입을 시도하지 않은 유저라는 의미다.
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.verify_email
def test_verify_email_if_code_is_registered(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
):
    code = secrets.token_urlsafe(10)  # 인증 코드 생성
    user_service.update(
        db_session,
        user=fake_user["user"],
        data_to_be_updated={"verification_code": code},
    )  # 유저 정보에 인증 코드 저장

    # 이메일 인증 및 결과
    response = client.post(f"{settings.API_V1_PREFIX}/verification-email/{code}")
    result_status_text = response.json()["status"]
    result_message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_message == "이메일 인증이 완료되었습니다."


@pytest.mark.login
def test_login_if_user_is_not_verified(client: TestClient, fake_user: Dict):
    # fake_user 정보
    login_data = fake_user["login_data"]

    # 로그인 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/login",
        json={"email": login_data["email"], "password": login_data["password"]},
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_message == "인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요."


@pytest.mark.login
def test_login_if_login_information_is_wrong(client: TestClient, fake_user: Dict):
    # fake_user 정보
    user = fake_user["user"]

    # 로그인 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/login",
        json={"email": user.email, "password": random_lower_string(k=8)},
    )
    result_message = response.json()["detail"]  # 로그인 결과

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_message == "입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다."


@pytest.mark.login
def test_login_if_user_registered(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
):
    # fake_user 정보
    user = fake_user["user"]
    login_data = fake_user["login_data"]

    # token 생성
    access_token_01 = user_service.create_access_token(data={"sub": user.email})
    email_01 = user_service.get_current_user(db_session, access_token_01)

    # verified 업데이트
    user_service.update(db_session, user, {"verified": True})

    # 로그인 및 결과
    response = client.post(
        f"{settings.API_V1_PREFIX}/login",
        json={"email": login_data["email"], "password": login_data["password"]},
    )
    access_token_02 = response.json()["access_token"]
    token_type = response.json()["token_type"]
    email_02 = user_service.get_current_user(db_session, access_token_02)

    assert response.status_code == status.HTTP_200_OK
    assert token_type == "Bearer"
    assert email_01 == email_02


@pytest.mark.reset_password
def test_reset_password_if_not_verified_email(client: TestClient, fake_user: Dict):
    # fake_user 정보
    user = fake_user["user"]

    # 패스워드 초기화 및 결과
    response = client.patch(f"{settings.API_V1_PREFIX}/password-reset", json=user.email)
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_message == "인증 완료되지 못한 이메일입니다. 먼저 이메일 인증을 완료하세요."


@pytest.mark.reset_password
def test_reset_password_if_not_user(client: TestClient):
    # 등록되지 않은 이메일 정보
    not_registered_email = random_email()

    # 패스워드 초기화 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/password-reset",
        json=not_registered_email,
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.reset_password
def test_reset_password_if_registered(
    client: TestClient,
    db_session: Session,
    fake_user: Dict,
):
    # fake_user 정보
    user = fake_user["user"]

    # verified 값 true로 변경
    user_service.update(db_session, user, {"verified": True})

    # 패스워드 초기화 및 결과
    response = client.patch(f"{settings.API_V1_PREFIX}/password-reset", json=user.email)

    result_status_text = response.json()["status"]
    result_message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_message == "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."


@pytest.mark.change_password
def test_change_password_if_password_is_wrong(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    wrong_password = random_lower_string(k=8)

    # 패스워드 변경 정보
    password_to_be_changed = UserPasswordUpdate(
        current_password=wrong_password,
        new_password=random_lower_string(k=8),
    )

    # 패스워드 초기화 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/password-change",
        headers=headers,
        json=password_to_be_changed.dict(),
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_message == "입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다."


@pytest.mark.change_password
def test_change_password_if_password_is_not_wrong(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    login_data = get_user_token_headers_and_login_data["login_data"]

    # password 변경 정보
    password_to_be_changed = UserPasswordUpdate(
        current_password=login_data["password"],
        new_password=random_lower_string(k=8),
    )

    # password 변경하기
    response = client.patch(
        f"{settings.API_V1_PREFIX}/password-change",
        headers=headers,
        json=password_to_be_changed.dict(),
    )
    result_status_text = response.json()["status"]
    result_message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_message == "비밀번호가 변경되었습니다."


@pytest.mark.read_user
def test_read_user_if_not_registered(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
):
    headers = get_user_token_headers_and_login_data["headers"]  # current_user 정보

    # 유저 조회 및 결과
    user_id = randint(2, 10)  # 임의로 생성한 user_id
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}", headers=headers)
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_message == "해당되는 유저를 찾을 수 없습니다."


@pytest.mark.read_user
def test_read_user_if_user_is_not_same_as_current_user(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
    fake_user: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    # 다른 유저 조회 및 결과
    other_user = fake_user["user"]
    response = client.get(
        f"{settings.API_V1_PREFIX}/users/{other_user.id}",
        headers=headers,
    )
    result = response.json()

    assert "email" not in result
    assert "password" not in result
    assert "id" in result
    assert "name" in result
    assert "profile_text" in result


@pytest.mark.read_user
def test_read_user_if_user_is_same_as_current_user(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    current_user_data = get_user_token_headers_and_login_data["login_data"]
    current_user_email = current_user_data["email"]

    # 동일한 유저 정보 조회 및 결과
    user_id = user_service.get_user(db_session, email=current_user_email).id
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}", headers=headers)
    result = response.json()
    email_of_user_id = result["email"]

    assert "email" in result
    assert "name" in result
    assert "profile_text" in result
    assert "password" not in result
    assert "profile_image_name" not in result
    assert "profile_image_path" not in result
    assert "verified" not in result
    assert "verification_code" not in result
    assert "created_at" not in result
    assert "updated_at" not in result
    assert current_user_email == email_of_user_id


@pytest.mark.update_user
def test_update_user_on_profile_text_if_not_authorized(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
    fake_user: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    current_user_data = get_user_token_headers_and_login_data["login_data"]
    current_user_email = current_user_data["email"]

    # 다른 유저 정보
    not_authorized_user = fake_user["user"]
    email_of_not_authorized_user = not_authorized_user.email

    # 변경할 유저 정보
    data_to_be_updated = UserUpdate(profile_text="Hello world")

    # 변경 시도 및 결과
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{not_authorized_user.id}",
        headers=headers,
        json=data_to_be_updated.dict(),
    )
    result_message = response.json()["detail"]

    assert current_user_email != email_of_not_authorized_user
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "수정할 권한이 없습니다."


@pytest.mark.update_user
def test_update_user_on_profile_text_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    current_user_data = get_user_token_headers_and_login_data["login_data"]
    current_user_email = current_user_data["email"]

    # 동일한 유저의 프로필 정보 변경
    user = user_service.get_user(db_session, email=current_user_email)
    info_to_be_updated = UserUpdate(profile_text="Hello world")
    response = client.patch(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=headers,
        json=info_to_be_updated.dict(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert user.profile_text == "Hello world"


@pytest.mark.delete_user
def test_delete_user_if_not_authorized(
    client: TestClient,
    get_user_token_headers_and_login_data: Dict,
    fake_user: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]

    # 유저 삭제 및 결과
    not_authorized_user = fake_user["user"]
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{not_authorized_user.id}",
        headers=headers,
    )
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_message == "삭제할 권한이 없습니다."


@pytest.mark.delete_user
def test_delete_user_if_authorized(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: Dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data["headers"]
    current_user_data = get_user_token_headers_and_login_data["login_data"]
    current_user_email = current_user_data["email"]

    # 유저 삭제 및 결과
    user = user_service.get_user(db_session, email=current_user_email)
    response = client.delete(
        f"{settings.API_V1_PREFIX}/users/{user.id}",
        headers=headers,
    )
    result_status_text = response.json()["status"]
    result_message = response.json()["message"]

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_message == "계정이 삭제되었습니다."


@pytest.mark.read_followers
def test_read_followers(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
):
    for user_id in range(1, 11):
        response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/followers")
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 9

        for user in result:
            assert "id" in user
            assert "email" in user


@pytest.mark.read_followers
def test_read_followers_if_not_exist_follower(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
):
    user_id = fake_user["user"].id
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/followers")
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_message == "해당 유저는 팔로워가 없습니다."


@pytest.mark.read_followings
def test_read_followings(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
):
    for user_id in range(1, 11):
        response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/followings")
        result = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert len(result) == 9

        for user in result:
            assert "id" in user
            assert "email" in user


@pytest.mark.read_followings
def test_read_followings_if_not_exist_following(
    client: TestClient,
    db_session: Session,
    fake_user: dict,
):
    user_id = fake_user["user"].id
    response = client.get(f"{settings.API_V1_PREFIX}/users/{user_id}/followings")
    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert result_message == "해당 유저는 팔로잉이 없습니다."


@pytest.mark.follow_user
def test_follow_user_if_success(
    client: TestClient,
    db_session: Session,
    fake_multi_user: None,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # follow 요청 및 결과
    for user_id in range(1, 11):
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/follow",
            headers=headers,
        )
        result_status_text = response.json().get("status")
        result_message = response.json().get("message")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_message == "follow 관계 맺기에 성공했습니다."


@pytest.mark.follow_user
def test_follow_user_if_already_follow(
    client: TestClient,
    db_session: Session,
    fake_multi_user: None,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    for user_id in range(1, 11):
        # 팔로우 신청
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/follow",
            headers=headers,
        )

        # 팔로우 재신청
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/follow",
            headers=headers,
        )

        result_message = response.json()["detail"]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert result_message == "이미 Follow 관계가 맺어져 있습니다."


@pytest.mark.unfollow_user
def test_unfollow_user_if_success(
    client: TestClient,
    db_session: Session,
    fake_multi_user: None,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    for user_id in range(1, 11):
        # follow 요청
        client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/follow",
            headers=headers,
        )

        # unfollow 요청 및 결과
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/unfollow",
            headers=headers,
        )
        result_status_text = response.json().get("status")
        result_message = response.json().get("message")

        assert response.status_code == status.HTTP_200_OK
        assert result_status_text == "success"
        assert result_message == "follow 관계 취소에 성공했습니다."


@pytest.mark.unfollow_user
def test_unfollow_user_if_already_unfollow(
    client: TestClient,
    db_session: Session,
    get_user_token_headers_and_login_data: dict,
    fake_follow: None,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # unfollow 대상 유저 정보
    user_id = 2

    # 중복으로 언팔로우 하기
    for _ in range(2):
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/unfollow",
            headers=headers,
        )

    result_message = response.json()["detail"]

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_message == "이미 Follow 관계가 취소되었습니다."


@pytest.mark.unfollow_user
def test_unfollow_user_if_not_found_follow(
    client: TestClient,
    db_session: Session,
    fake_follow: None,
    get_user_token_headers_and_login_data: dict,
):
    # current_user 정보
    headers = get_user_token_headers_and_login_data.get("headers")

    # unfollow 대상 유저 정보
    for user_id in range(1, 11):
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/{user_id}/unfollow",
            headers=headers,
        )
        result_message = response.json()["detail"]

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert result_message == "해당 정보에 일치하는 Follow 관계를 찾을 수 없습니다."
