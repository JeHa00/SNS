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
        self._redis_engine = None
        self._redis_session = None

    def init_app(self, app: FastAPI, **kwargs):
        """
        db 초기화 함수
        """
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

        self._redis_engine = redis.ConnectionPool(
            host=settings.REDIS_DB_HOST,
            port=settings.REDIS_DB_PORT,
        )

        self._redis_session = redis.Redis(
            connection_pool=self._redis_engine,
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
        요청마다 DB 세션 유지하는 함수
        """
        if self._session is None:
            self.init_app(self._app)

        db_session = self._session()

        try:
            yield db_session
        except Exception:
            db_session.rollback()
        finally:
            db_session.close()

    def get_redis_db(self):
        if self._redis_session is None:
            self.init_app(self._app)
        try:
            redis_db_session = self._redis_session
            yield redis_db_session
        finally:
            redis_db_session.close()

    @property
    def engine(self):
        return self._engine


db = SQLAlchemy()
