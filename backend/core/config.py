from typing import List
from pathlib import Path
import secrets 

from pydantic import BaseSettings, SecretStr, AnyHttpUrl


BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    PROJECT_NAME: str = 'SNS'
    API_V1_STR: str = '/api/v1'

    DB_USERNAME: str = 'root'
    DB_PASSWORD: SecretStr = 'a1s2s3d4'
    DB_HOST: str = '127.0.0.1'
    DB_PORT: int = '3306'
    DB_NAME: str = 'SNS_02'
    SQLALCHEMY_DATABASE_URI: str = "mysql+pymysql://{username}:{password}@{host}:{port}/{name}?charset=utf8mb4"

    SECRET_KEY: str = secrets.token_urlsafe(32)
    SECRET_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    class config:
        env_file = BASE_DIR / 'env'


settings = Settings()
