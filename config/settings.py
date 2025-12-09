import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Atomic service URLs
    INTEGRATIONS_SERVICE_URL: str = os.getenv(
        "https://integrations-svc-ms2-ft4pa23xra-uc.a.run.app",
        "http://localhost:8001"
    )
    ACTIONS_SERVICE_URL: str = os.getenv(
        "ACTIONS_SERVICE_URL",
        "http://localhost:8002"
    )
    CLASSIFICATION_SERVICE_URL: str = os.getenv(
        "CLASSIFICATION_SERVICE_URL",
        "http://localhost:8003"
    )
    
    # Request timeout in seconds
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Database connection settings (for coordination)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/composite_db"
    )
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()

