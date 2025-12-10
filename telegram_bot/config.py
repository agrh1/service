import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    API_GATEWAY_URL: str = "http://api_gateway:8003"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    METRICS_PORT: int = 9102
    
    class Config:
        env_file = '.env'

settings = Settings()
