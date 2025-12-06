import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # IntraService
    INTRASERVICE_URL: str
    INTRASERVICE_USERNAME: str
    INTRASERVICE_PASSWORD: str
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = '.env'

settings = Settings()

