from typing import Dict
import pytest
import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client
from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate
from sns.users.service import user_service


@pytest.fixture(scope="function")
def fake_user(client: TestClient, db_session: Session):
    password = random_lower_string(k=8)
    signup_data = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    login_data = copy.deepcopy(signup_data)

    user = user_service.create(db_session, data_for_signup=signup_data)
    return {"user": user, "login_data": login_data}


@pytest.fixture(scope="function")
def get_user_token_headers_and_login_data(
    client: TestClient, db_session: Session
) -> Dict:
    # fake_user 생성
    email = random_email()
    password = random_lower_string(k=8)
    signup_data = UserCreate(email=email, password=password, password_confirm=password)
    fake_user = user_service.create(db_session, data_for_signup=signup_data)

    # verified 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    user_service.update(db_session, fake_user, info_to_be_updated)

    # 로그인
    login_data = {"email": email, "password": password}
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    # headers 반환
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "login_data": login_data}
