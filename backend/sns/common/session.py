from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, close_all_sessions

from sns.common.config import settings


class SQLAlchemy:
    def __init__(self):
        self._engine = None
        self._session = None
        self._app = None

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

        @app.on_event("startup")
        def startup():
            self._engine.connect()

        @app.on_event("shutdown")
        def shutdown():
            close_all_sessions()
            self._engine.dispose()

    def get_db(self):
        """
        요청마다 DB 세션 유지하는 함수
        """
        if self._session is None:
            self.init_app(self._app)
        try:
            db_session = self._session()
            yield db_session
        finally:
            db_session.close()

    @property
    def engine(self):
        return self._engine


db = SQLAlchemy()
