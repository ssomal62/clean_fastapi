from pydantic_settings import BaseSettings, SettingsConfigDict


class UserSettings(BaseSettings):
    """User 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 사용자 설정
    DEFAULT_USER_ROLE: str = "user"
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 64
    NAME_MAX_LENGTH: int = 32
    EMAIL_MAX_LENGTH: int = 64


user_settings = UserSettings()
