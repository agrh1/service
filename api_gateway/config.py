from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Services URLs
    INTRASERVICE_URL: str = "http://intraservice:8001"
    SEAFILE_SERVICE_URL: str = "http://seafile:8002"
    DJANGO_URL: str = "http://django:8000"
    
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8003
    
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    class Config:
        env_file = '.env'

settings = Settings()

