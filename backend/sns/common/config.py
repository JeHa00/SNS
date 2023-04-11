from pydantic import BaseSettings, SecretStr, AnyHttpUrl
from typing import List
import secrets
from sns.common.path import BASE_DIR


class Settings(BaseSettings):
    PJT_NAME: str = "SNS"
    API_V1_STR: str = "/api/v1"

    DB_USERNAME: str = "pjt"
    DB_PASSWORD: SecretStr = "a1s2d3f4"
    DB_HOST: str = "db.mysql"
    DB_PORT: int = "3306"
    DB_NAME: str = "sns"

    SQLALCHEMY_DATABASE_URI: str = (
        "mysql+pymysql://{username}:{pw}@{host}:{port}/{name}?charset=utf8mb4"
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    SECRET_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_TLS: str = True
    SMTP_PORT: int = 587 if SMTP_TLS else 465
    EMAIL_ADDR = "only.for.pjt@gmail.com"
    EMAIL_PASSWORD = "wngvlgolokntjpas"

    def get_test_db_url(self):
        db_username: str = "root"
        db_host: str = "0.0.0.0"
        db_name: str = "test"
        db_port: str = "3310"

        return self.SQLALCHEMY_DATABASE_URI.format(
            username=db_username,
            pw=self.DB_PASSWORD.get_secret_value(),
            host=db_host,
            port=db_port,
            name=db_name,
        )

    class config:
        env_file = BASE_DIR / "env"


settings = Settings()
