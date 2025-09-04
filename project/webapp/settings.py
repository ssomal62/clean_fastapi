from pydantic_settings import BaseSettings, SettingsConfigDict


class WebAppSettings(BaseSettings):
    """WebApp 도메인 설정"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 애플리케이션 설정
    APP_NAME: str = "Clean FastAPI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API 설정
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    
    # CORS 설정
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # 보안 설정
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 성능 모니터링 설정
    ENABLE_PERFORMANCE_MONITORING: bool = True
    SLOW_REQUEST_THRESHOLD: float = 1.0  # seconds
    
    # 페이지네이션 설정
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 100


settings = WebAppSettings()
