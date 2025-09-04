from pydantic_settings import BaseSettings, SettingsConfigDict


class InfrastructureSettings(BaseSettings):
    """Infrastructure 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment
    ENVIRONMENT: str = "development"
    
    # Performance
    ENABLE_PERFORMANCE_MONITORING: bool = True
    SLOW_REQUEST_THRESHOLD: float = 1.0  # seconds
    
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Settings
    EMAIL_ADDRESS: str
    APP_PASSWORD: str
    
    # Celery Settings
    CELERY_BROKER_URL: str
    CELERY_BACKEND_URL: str
    BROKER_CONNECTION_RETRY_ON_STARTUP: bool = True
    
    # RabbitMQ Settings
    RABBITMQ_URL: str


infrastructure_settings = InfrastructureSettings()
