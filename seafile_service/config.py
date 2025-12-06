from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    SEAFILE_URL: str
    SEAFILE_USERNAME: str
    SEAFILE_PASSWORD: str
    SEAFILE_LIBRARY_ID: str
    
    REDIS_URL: str = "redis://redis:6379/0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8002
    
    class Config:
        env_file = '.env'

settings = Settings()
