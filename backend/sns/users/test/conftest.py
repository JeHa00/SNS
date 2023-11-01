from typing import Dict, Any
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# flake8: noqa
from sns.common.conftest import start_app, app, db_session, client, redis_db_session
from sns.common.config import settings
from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserCreate
from sns.users.repositories.db import user_crud
from sns.users.service import user_service


@pytest.fixture(scope="function")
def fake_user(
    client: TestClient,
    db_session: Session,
) -> Dict[str, Any]:
    """
    테스트용 유저 1명을 생성한다. 이 유저는 이메일 인증이 안되어 있고, 로그인하지 않은 상태이다.
    테스트 시 로그인 유저가 필요할 경우, 이 fixture를 사용하여 로그인 상황을 만들 수 있다.
    전달되는 값은 User model 정보와 로그인 정보를 전달한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
    """
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
) -> Dict[str, Any]:
    """
    로그인한 유저 1명을 생성한다. 로그인했으므로 Bearer token을 발행받아 header로 전달한다.
    전달되는 값은 인증 토큰이 있는 header와 로그인 정보를 전달한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
    """
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
def fake_multi_user(
    client: TestClient,
    db_session: Session,
) -> None:
    """
    로그인하지 않은 상태이고, 이메일 인증된 테스트용 유저 10명을 생성한다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
    """
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
def fake_follow(
    client: TestClient,
    db_session: Session,
    fake_multi_user: None,
) -> None:
    """
    fake_multi_user fixture를 사용하여 테스트용 팔로우 데이터를 81개 생성한다.
    81개인 이유는 10명의 유저가 자신을 제외한 나머지 유저를 팔로우하기 때문이다.

    Args:
        client (TestClient): test용 db url에 연결된 client를 생성
        db_session (Session): db session.
        fake_multi_user (None): 테스트용 유저 10명을 생성
    """
    for following_id in range(1, 11):
        for follower_id in range(1, 11):
            if following_id == follower_id:
                continue
            follow_data = {"following_id": following_id, "follower_id": follower_id}
            user_crud.follow(db_session, None, **follow_data)
