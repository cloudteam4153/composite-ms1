import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Atomic service URLs - defaults to localhost for local development
    INTEGRATIONS_SERVICE_URL: str = "http://localhost:8001"
    ACTIONS_SERVICE_URL: str = "http://localhost:8002"
    CLASSIFICATION_SERVICE_URL: str = "http://localhost:8003"
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/composite_db"
    
    # Request timeout in seconds
    REQUEST_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()

