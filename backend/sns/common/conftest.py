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
def start_app() -> FastAPI:
    app = FastAPI()
    app.include_router(users, tags=["Users"], prefix=settings.API_V1_PREFIX)
    app.include_router(posts, tags=["Posts"], prefix=settings.API_V1_PREFIX)
    # app.include_router(comments, tags=["Comments"], prefix=settings.API_V1_PREFIX)
    return app


@pytest.fixture(scope="function")
def app(start_app: FastAPI) -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case
    """
    Base.metadata.create_all(bind=engine)
    yield start_app
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
