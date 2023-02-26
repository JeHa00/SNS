from fastapi import FastAPI
from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import logging

from core.config import settings 

class SQLAlchemy:
    def __init__(self, app: FastAPI = None, **kwargs):
        self._engine = None
        self._session = None 
        if app is not None:
            self.init_app(app=app, **kwargs)


    def init_app(self, app: FastAPI, **kwargs):
        """
        db 초기화 함수  
        """
        self._engine = create_engine(
            "mysql+pymysql://{username}:{password}@{host}:{port}/{name}?charset=utf8mb4".format(
                username=settings.DB_USERNAME,
                password=settings.DB_PASSWORD.get_secret_value(),
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                name=settings.DB_NAME,
            )
        )

        self._session = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)

        @app.on_event('startup')
        def startup(self):
            self._engine.connect() 
            logging.info('DB connected')

        @app.on_event('shutdown')
        def shutdown(self):
            self._session.close_all()
            self._engine.dispose() 
            logging.info("DB disconnected")


    def get_db(self):
        """
        요청마다 DB 세션 유지하는 함수 
        """
        if self._session is None: 
            raise Exception("must bt called 'init_app'")
        try:
            db_session = self._session()
            yield db_session 
        finally:
            db_session.close()  

    @property 
    def session(self):
        return self.get_db 

    @property
    def engine(self):
        return self._engine

db = SQLAlchemy()
Base = declarative_base()
