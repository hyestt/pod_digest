from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/pod_digest"
    
    # OpenAI
    openai_api_key: str
    
    # Beehiiv
    beehiiv_api_key: str
    beehiiv_publication_id: str
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # App settings
    app_name: str = "Podcast Digest"
    debug: bool = False
    frontend_url: str = "http://localhost:3000"
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()