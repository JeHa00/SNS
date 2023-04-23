from typing import Dict
import pytest
import copy

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client
from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate
from sns.users.repositories.db import user_crud
from sns.users.service import user_service


@pytest.fixture(scope="function")
def fake_user(client: TestClient, db_session: Session):
    password = random_lower_string(k=8)
    signup_data = UserCreate(
        email=random_email(),
        password=password,
        password_confirm=password,
    )

    user = user_service.create(db_session, signup_data.dict())
    return {"user": user, "login_data": signup_data.dict()}


@pytest.fixture(scope="function")
def get_user_token_headers_and_login_data(
    client: TestClient,
    db_session: Session,
) -> Dict:
    # fake_user 생성
    email = random_email()
    password = random_lower_string(k=8)
    signup_data = UserCreate(email=email, password=password, password_confirm=password)
    fake_user = user_service.create(db_session, signup_data.dict())

    # verified 업데이트
    user_service.update(db_session, fake_user, {"verified": True})

    # 로그인
    login_data = {"email": email, "password": password}
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_data)

    # headers 반환
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "login_data": login_data}


@pytest.fixture(scope="function")
def fake_multi_user(client: TestClient, db_session: Session):
    for _ in range(10):
        # fake_user 생성
        email = random_email()
        password = random_lower_string(k=8)
        signup_data = UserCreate(
            email=email,
            password=password,
            password_confirm=password,
        )
        fake_user = user_service.create(db_session, signup_data.dict())

        # verified 업데이트
        user_service.update(db_session, fake_user, {"verified": True})


@pytest.fixture(scope="function")
def fake_follow(client: TestClient, db_session: Session, fake_multi_user: None):
    for following_id in range(1, 11):
        for follower_id in range(1, 11):
            if following_id == follower_id:
                continue
            follow_data = {"following_id": following_id, "follower_id": follower_id}
            user_crud.follow(db_session, None, **follow_data)
