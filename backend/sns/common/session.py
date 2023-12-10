from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions
import redis

from sns.common.config import settings
from sns.common.base import Base


class SQLAlchemy:
    def __init__(self):
        self._engine = None
        self._session = None
        self._app = None

    def init_app(self, app: FastAPI, **kwargs):
        """
        db 초기화 함수
        """
        self._app = app
        self._engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URI.format(
                username=settings.DB_USERNAME,
                pw=settings.DB_PASSWORD.get_secret_value(),
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                name=settings.DB_NAME,
            ),
        )

        self._session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

        @app.on_event("startup")
        def startup():
            self._engine.connect()

        @app.on_event("shutdown")
        def shutdown():
            close_all_sessions()
            self._engine.dispose()

        Base.metadata.create_all(bind=self._engine)

    def get_db(self):
        """
        요청마다 DB 세션을 반환한다.
        """
        if self._session is None:
            self.init_app(self._app)

        return self._session()

    @property
    def engine(self):
        return self._engine


class RedisDB:
    def __init__(self):
        self._app = None
        self._redis_engine = None
        self._redis_session = None

    def init_app(self, app: FastAPI):
        self._app = app

        self._redis_engine = redis.ConnectionPool(
            host=settings.REDIS_DB_HOST,
            port=settings.REDIS_DB_PORT,
        )

        self._redis_session = redis.Redis(
            connection_pool=self._redis_engine,
        )

    def get_db(self):
        if self._redis_session is None:
            self.init_app(self._app)
        try:
            yield self._redis_session
        finally:
            self._redis_session.close()


db = SQLAlchemy()
redis_db = RedisDB()
