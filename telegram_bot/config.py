from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    API_GATEWAY_URL: str = "http://api_gateway:8003"
    API_GATEWAY_TIMEOUT: float = 15.0

    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "telegram_bot"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    ENABLE_THREAD_NOTIFICATIONS: bool = False
    ENABLE_ADMIN_THREAD_NOTIFICATIONS: bool = False
    THREAD_TOPIC_ID: Optional[int] = None

    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = '.env'


settings = Settings()
