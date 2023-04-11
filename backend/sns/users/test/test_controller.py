import pytest
import secrets
from random import randint

from fastapi import status
from fastapi.encoders import jsonable_encoder

from sns.common.config import settings
from sns.users.test.utils import random_email, random_lower_string
from sns.users.schema import UserCreate, UserUpdate, UserPasswordUpdate
from sns.users.service import create_access_token, create, update, get_user


@pytest.mark.signup
def test_signup_if_password_is_not_same_as_password_confirm(client):
    # 서로 다른 password 생성
    password = random_lower_string(k=8)
    password_confirm = random_lower_string(k=8)
    while password == password_confirm:
        password = random_lower_string(k=8)
        password_confirm = random_lower_string(k=8)

    # 회원가입 정보
    signup_info = UserCreate(
        email=random_email(), password=password, password_confirm=password_confirm
    )

    # 회원가입 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/signup", json=jsonable_encoder(signup_info)
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_msg == "비밀번호 정보가 일치하지 않습니다."


@pytest.mark.signup
def test_signup_if_email_is_not_verified(client, db_session):
    # fake_user 생성
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    create(db_session, user_info=user_info)

    # 회원가입 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/signup", json=jsonable_encoder(user_info)
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "인증 완료되지 못한 이메일입니다."


@pytest.mark.signup
def test_signup_if_email_is_already_verified(client, db_session):
    # fake_user 생성
    email = random_email()
    password = random_lower_string(k=8)
    user_info = UserCreate(email=email, password=password, password_confirm=password)
    user = create(db_session, user_info=user_info)

    # verified 정보 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, user, info_to_be_updated)

    # 회원가입 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/signup", json=jsonable_encoder(user_info)
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "이미 인증된 이메일입니다."


@pytest.mark.verify_email
def test_verify_email_if_code_is_not_registered(client):
    code = secrets.token_urlsafe(10)  # 인증 코드 생성

    # 이메일 인증 및 결과
    response = client.patch(f"{settings.API_V1_STR}/verification-email/{code}")
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록되지 않은 인증 링크입니다."


@pytest.mark.verify_email
def test_verify_email_if_code_is_registered(client, db_session, fake_user):
    code = secrets.token_urlsafe(10)  # 인증 코드 생성
    update(
        db_session, user=fake_user.get("user"), user_info={"verification_code": code}
    )  # 유저 정보에 인증 코드 저장

    # 이메일 인증 및 결과
    response = client.patch(f"{settings.API_V1_STR}/verification-email/{code}")
    result_status_text = response.json().get("status")
    result_msg = response.json().get("msg")

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "이메일 인증이 완료되었습니다."


@pytest.mark.login
def test_login_if_user_is_not_verified(client, fake_user):
    # fake_user 정보
    user = fake_user.get("user")
    user_info = fake_user.get("user_info")

    # 로그인 정보
    login_info = {'email': user.email, 'password': user_info.password}

    # 로그인 및 결과
    response = client.post(f"{settings.API_V1_STR}/login", json=login_info)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "먼저 이메일 인증을 완료하세요."


@pytest.mark.login
def test_login_if_login_info_is_wrong(client, fake_user):
    # fake_user 정보
    user = fake_user.get("user")

    # 로그인 정보
    login_info = {"email": user.email, "password": random_lower_string(k=8)}    

    # 로그인 및 결과
    response = client.post(f"{settings.API_V1_STR}/login", json=login_info)
    result_msg = response.json().get("detail")  # 로그인 결과

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert result_msg == "이메일 또는 비밀번호 정보가 정확하지 않습니다."


@pytest.mark.login
def test_login_if_user_registered(client, db_session, fake_user):
    # fake_user 정보
    user = fake_user.get("user")
    user_info = fake_user.get("user_info")
    access_token_1 = create_access_token(data={"sub": user.email})  # token 생성

    # verified 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, user, info_to_be_updated)

    # 로그인 정보
    login_info = {'email': user.email, 'password': user_info.password}

    # 로그인 및 결과
    response = client.post(f"{settings.API_V1_STR}/login", json=login_info)
    access_token_2 = response.json().get("access_token")
    token_type = response.json().get("token_type")

    assert response.status_code == status.HTTP_200_OK
    assert access_token_1 == access_token_2
    assert token_type == "Bearer"


@pytest.mark.reset_password
def test_reset_password_if_not_verified_email(client, fake_user):
    # fake_user 정보
    user = fake_user.get("user")

    # 패스워드 초기화 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/password-reset", json=user.email
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "먼저 이메일 인증을 완료하세요."


@pytest.mark.reset_password
def test_reset_password_if_not_user(client):
    # 등록되지 않은 이메일 정보
    not_registered_email = random_email()

    # 패스워드 초기화 및 결과
    response = client.post(f"{settings.API_V1_STR}/password-reset", json=not_registered_email)
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert result_msg == "등록된 회원이 아닙니다."


@pytest.mark.reset_password
def test_reset_password_if_registered(client, db_session, fake_user):
    # fake_user 정보
    user = fake_user.get("user")

    # verified 값 true로 변경
    info_to_be_updated = UserUpdate(verified=True, profile_text=None)
    update(db_session, user, info_to_be_updated)

    # 패스워드 초기화 및 결과
    response = client.post(
        f"{settings.API_V1_STR}/password-reset", json=user.email
    )
    result_status_text = response.json().get("status")
    result_msg = response.json().get("msg")

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "비밀번호 초기화를 위한 이메일 송신이 완료되었습니다."


@pytest.mark.change_password
def test_change_password_if_password_is_not_same_as_password_confirm(
    client, get_user_token_headers_and_user_info
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")
    wrong_password = random_lower_string(k=8)

    # 패스워드 변경 정보
    password_info = UserPasswordUpdate(
        current_password=wrong_password, new_password=random_lower_string(k=8)
    )
    data = {**password_info.dict(), "current_user": jsonable_encoder(user_info)}

    # 패스워드 초기화 및 결과
    response_2 = client.patch(
        f"{settings.API_V1_STR}/password-change", headers=headers, json=data
    )
    result_msg = response_2.json().get("detail")

    assert response_2.status_code == status.HTTP_400_BAD_REQUEST
    assert result_msg == "입력한 비밀번호가 기존 비밀번호와 일치하지 않습니다."


@pytest.mark.change_password
def test_change_password_if_password_is_same_as_password_confirm(
    client, get_user_token_headers_and_user_info
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    user_info = get_user_token_headers_and_user_info.get("user_info")

    # password 변경 정보
    password_info = UserPasswordUpdate(
        current_password=user_info.get("password"),
        new_password=random_lower_string(k=8),
    )
    data = {**password_info.dict(), "current_user": jsonable_encoder(user_info)}

    # password 변경하기
    response = client.patch(
        f"{settings.API_V1_STR}/password-change", headers=headers, json=data
    )
    result_status_text = response.json().get("status")
    result_msg = response.json().get("msg")

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "비밀번호가 변경되었습니다."


@pytest.mark.read_user
def test_read_user_if_not_registered(client, get_user_token_headers_and_user_info):
    headers = get_user_token_headers_and_user_info.get("headers")  # current_user 정보

    # 유저 조회 및 결과
    user_id = randint(2, 10)  # 임의로 생성한 user_id
    response = client.get(f"{settings.API_V1_STR}/users/{user_id}", headers=headers)
    result_msg = response.json().get("detail")

    assert response.status_code == 400
    assert result_msg == "등록되지 않은 유저입니다."


@pytest.mark.read_user
def test_read_user_if_user_is_not_same_as_current_user(
    client, get_user_token_headers_and_user_info, fake_user
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    current_user_info = get_user_token_headers_and_user_info.get("user_info")
    current_user_email = current_user_info.get("email")

    # 다른 유저 조회 및 결과
    other_user = fake_user.get("user")
    response = client.get(
        f"{settings.API_V1_STR}/users/{other_user.id}", headers=headers
    )
    email_of_other_user = response.json().get("email")

    assert current_user_email != email_of_other_user


@pytest.mark.read_user
def test_read_user_if_user_is_same_as_current_user(
    client, db_session, get_user_token_headers_and_user_info
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    current_user_info = get_user_token_headers_and_user_info.get("user_info")
    current_user_email = current_user_info.get("email")

    # 동일한 유저 정보 조회 및 결과
    user_id = get_user(db_session, email=current_user_email).id
    response = client.get(f"{settings.API_V1_STR}/users/{user_id}", headers=headers)
    email_of_user_id = response.json().get("email")

    assert current_user_email == email_of_user_id


@pytest.mark.update_user
def test_update_user_on_profile_text_if_not_authorized(
    client, get_user_token_headers_and_user_info, fake_user
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    current_user_info = get_user_token_headers_and_user_info.get("user_info")
    current_user_email = current_user_info.get("email")

    # 다른 유저 정보
    not_authorized_user = fake_user.get("user")
    email_of_not_authorized_user = not_authorized_user.email

    # 변경할 유저 정보
    info_to_be_updated = UserUpdate(profile_text="Hello world", verified=True)
    data = jsonable_encoder(info_to_be_updated)

    # 변경 시도 및 결과
    response = client.patch(
        f"{settings.API_V1_STR}/users/{not_authorized_user.id}",
        headers=headers,
        json=data,
    )
    result_msg = response.json().get("detail")

    assert current_user_email != email_of_not_authorized_user
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "수정할 권한이 없습니다."


@pytest.mark.update_user
def test_update_user_on_profile_text_if_authorized(
    client, db_session, get_user_token_headers_and_user_info
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    current_user_info = get_user_token_headers_and_user_info.get("user_info")
    current_user_email = current_user_info.get("email")

    # 동일한 유저의 프로필 정보 변경
    user = get_user(db_session, email=current_user_email)
    info_to_be_updated = UserUpdate(profile_text="Hello world", verified=True)
    data = jsonable_encoder(info_to_be_updated)
    response = client.patch(
        f"{settings.API_V1_STR}/users/{user.id}", headers=headers, json=data
    )

    assert response.status_code == status.HTTP_200_OK
    assert user.profile_text == "Hello world"


@pytest.mark.delete_user
def test_delete_user_if_not_authorized(
    client, get_user_token_headers_and_user_info, fake_user
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")

    # 유저 삭제 및 결과
    not_authorized_user = fake_user.get("user")
    response = client.delete(
        f"{settings.API_V1_STR}/users/{not_authorized_user.id}", headers=headers
    )
    result_msg = response.json().get("detail")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert result_msg == "삭제할 권한이 없습니다."


@pytest.mark.delete_user
def test_delete_user_if_authorized(
    client, db_session, get_user_token_headers_and_user_info
):
    # current_user 정보
    headers = get_user_token_headers_and_user_info.get("headers")
    current_user_info = get_user_token_headers_and_user_info.get("user_info")
    current_user_email = current_user_info.get("email")

    # 유저 삭제 및 결과
    user = get_user(db_session, email=current_user_email)
    response = client.delete(f"{settings.API_V1_STR}/users/{user.id}", headers=headers)
    result_status_text = response.json().get("status")
    result_msg = response.json().get("msg")

    assert response.status_code == status.HTTP_200_OK
    assert result_status_text == "success"
    assert result_msg == "계정이 삭제되었습니다."