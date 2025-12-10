import os
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # IntraService
    INTRASERVICE_URL: str = "http://intraservice"
    INTRASERVICE_USERNAME: str = "user"
    INTRASERVICE_PASSWORD: str = "password"
    INTRASERVICE_SEAF_USER: str = "seaf_user"
    INTRASERVICE_STATUS_IDS: List[int] = Field(default_factory=list)
    EVENTLOG_BASE_URL: str = "http://intraservice/eventlog.ivp"
    EVENTLOG_FILTER_PATTERNS: List[str] = Field(default_factory=list)
    EVENTLOG_BATCH_SIZE: int = 10

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Postgres
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"

    # Integrations
    BOT_WEBHOOK_URL: Optional[str] = None

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    @field_validator("INTRASERVICE_STATUS_IDS", mode="before")
    @classmethod
    def parse_status_ids(cls, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(v.strip()) for v in value.split(',') if v.strip()]
        return value

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

