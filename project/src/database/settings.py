from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database 연결 설정
    POSTGRES_URL: str
    DB_ECHO: bool = False
    
    # Connection Pool 설정
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Migration 설정
    DB_MIGRATION_AUTO: bool = False
    DB_MIGRATION_VERSION: str = "head"


database_settings = DatabaseSettings()
