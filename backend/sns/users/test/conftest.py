from typing import Dict
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client
from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate, UserUpdate, Follow
from sns.users.repositories.db import user_crud, follow_crud


@pytest.fixture(scope="function")
def fake_user(client, db_session):
    password = random_lower_string(k=8)
    user_info = UserCreate(
        email=random_email(), password=password, password_confirm=password
    )
    user = user_crud.create(db_session, user_info=user_info)
    return {"user": user, "user_info": user_info}


@pytest.fixture(scope="function")
def get_user_token_headers_and_user_info(client, db_session) -> Dict[str, str]:
    # fake_user 생성
    email = random_email()
    password = random_lower_string(k=8)
    user_info = UserCreate(email=email, password=password, password_confirm=password)
    fake_user = user_crud.create(db_session, user_info=user_info)

    # verified 업데이트
    info_to_be_updated = UserUpdate(verified=True)
    user_crud.update(db_session, fake_user, info_to_be_updated)

    # 로그인
    login_info = {"email": email, "password": password}
    response = client.post(f"{settings.API_V1_PREFIX}/login", json=login_info)

    # headers 반환
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "user_info": login_info}


@pytest.fixture(scope="function")
def fake_multi_user(client: TestClient, db_session: Session):
    for _ in range(10):
        # fake_user 생성
        email = random_email()
        password = random_lower_string(k=8)
        user_info = UserCreate(
            email=email, password=password, password_confirm=password
        )
        fake_user = user_crud.create(db_session, user_info=user_info)

        # verified 업데이트
        info_to_be_updated = UserUpdate(verified=True)
        user_crud.update(db_session, fake_user, info_to_be_updated)


@pytest.fixture(scope="function")
def fake_follow(client: TestClient, db_session: Session, fake_multi_user: None):
    for following_id in range(1, 11):
        for follower_id in range(1, 11):
            if following_id == follower_id:
                continue
            follow_info = Follow(following_id=following_id, follower_id=follower_id)
            follow_crud.follow(db_session, follow_info=follow_info)
