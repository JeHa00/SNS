from typing import Dict
import pytest

from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate
from sns.users.service import create, update
from sns.common.config import settings
from sns.common.conftest import app, db_session, client


@pytest.fixture(scope="function")
def fake_user(client, db_session):
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    user = create(db_session, user_info=user_info)
    return {"user": user, "user_info": user_info}


@pytest.fixture(scope="function")
def get_user_token_headers_and_user_info(client, db_session) -> Dict[str, str]:
    # fake_user 생성
    email = random_email()
    password = random_lower_string(k=8)
    user_info = UserCreate(email=email, password=password, password_confirm=password)
    fake_user = create(db_session, user_info=user_info)

    # verified 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    update(db_session, fake_user, info_to_be_updated)

    # 로그인
    login_info = {'email': email, 'password': password}
    response = client.post(f"{settings.API_V1_STR}/login", json=login_info)

    # headers 반환
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "user_info": login_info}