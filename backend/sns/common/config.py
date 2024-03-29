from pydantic import BaseSettings, SecretStr, AnyHttpUrl
from typing import List
import secrets
from sns.common.path import BASE_DIR


class Settings(BaseSettings):
    PROJECT_NAME: str = "SNS"
    API_V1_PREFIX: str = "/api/v1"

    # Mysql
    DB_USERNAME: str = "project"
    DB_PASSWORD: SecretStr = "a1s2d3f4"
    DB_HOST: str = "db.mysql"
    DB_PORT: str = "3306"
    DB_NAME: str = "sns"

    # REDIS
    REDIS_DB_HOST: str = "db.redis"
    REDIS_DB_PORT: str = "6379"

    SQLALCHEMY_DATABASE_URI: str = (
        "mysql+pymysql://{username}:{pw}@{host}:{port}/{name}?charset=utf8mb4"
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    SECRET_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587 if SMTP_TLS else 465
    EMAIL_ADDRESS = "only.for.pjt@gmail.com"
    EMAIL_PASSWORD = "mgfm vjkj mdzr jgcz"

    TIME_TO_RETRY_CONNECTION = 10000  # unit: millisecond

    class config:
        env_file = BASE_DIR / "env"


settings = Settings()
