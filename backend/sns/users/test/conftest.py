import pytest
from typing import Generator, Any, Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sns.users.test.utils import random_lower_string, random_email
from sns.users.schema import UserBase, UserCreate, UserUpdate
from sns.users.service import create, update
from sns.common.config import settings
from sns.common.session import db
from sns.common.base import Base
from sns.main import app as main_app


engine = create_engine(settings.get_test_db_url())
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case
    """
    Base.metadata.create_all(bind=engine)
    yield main_app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[TestingSessionLocal, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(app: FastAPI, db_session: TestingSessionLocal):
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[db.get_db] = _get_test_db
    with TestClient(app) as client:
        yield client


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
    login_info = UserBase(email=email, password=password)
    data = jsonable_encoder(login_info)
    response = client.post(f"{settings.API_V1_STR}/login", json=data)

    # headers 반환
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    return {"headers": headers, "user_info": data}
