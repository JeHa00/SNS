from typing import Generator, Any
import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sns.common.config import settings
from sns.common.session import db
from sns.common.base import Base
from sns.users.controller import router as users
from sns.posts.controller import router as posts

# from sns.comments.controller import router as comments

engine = create_engine(settings.get_test_db_url())
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def start_app(start_app: FastAPI) -> Generator[FastAPI, Any, None]:
    """
    test db와 연결된 app을 생성하여 기존에 만들었던 router를 연결한다.
    """
    app = FastAPI()
    app.include_router(users, tags=["Users"], prefix=settings.API_V1_PREFIX)
    app.include_router(posts, tags=["Posts"], prefix=settings.API_V1_PREFIX)
    # app.include_router(comments, tags=["Comments"], prefix=settings.API_V1_PREFIX)
    return app


@pytest.fixture(scope="function")
def app(start_app: FastAPI) -> Generator[FastAPI, Any, None]:
    """
    각 테스트 케이스마다 테스트용 database와 table을 새로 생성하고 삭제한다.
    """
    Base.metadata.create_all(bind=engine)
    yield start_app
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[TestingSessionLocal, Any, None]:
    """
    test db에 연결된 connection을 생성하고, session을 반환한다.
    """
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
    테스트 전용 db fixture를 사용하는 FastAPI의 TestClient를 생성한다.
    테스트 전용 db를 사용하기 위해서 기존에 'get_db'를 오버라이딩하여 매 테스트 케이스마다 db_session을 호출한다.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[db.get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
