from pydantic_settings import BaseSettings, SettingsConfigDict

from ..shared.settings import shared_settings


class AuthSettings(BaseSettings):
    """Auth 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # JWT 설정 (shared에서 가져옴)
    SECRET_KEY: str = shared_settings.SECRET_KEY
    ALGORITHM: str = shared_settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES: int = shared_settings.ACCESS_TOKEN_EXPIRE_MINUTES

auth_settings = AuthSettings()
