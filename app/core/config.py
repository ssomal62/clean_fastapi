from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_url: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    email_address: str
    app_password: str
    celery_broker_url: str
    celery_backend_url: str

    class Config:
        env_file = ".env"

settings = Settings()