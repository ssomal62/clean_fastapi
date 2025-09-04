import os
from dependency_injector import containers, providers

from .argon2_password_hasher import Argon2PasswordHasher
from .email_sender import SendWelcomeEmailTask
from .jwt_provider import JwtProvider
from .celery_app import create_celery_app
from .settings import InfrastructureSettings
from .unit_of_work import SqlAlchemyUnitOfWork

class InfrastructureContainer(containers.DeclarativeContainer):
    """공통 인프라 계층 컨테이너 - 데이터베이스, 외부 서비스 등"""
    settings = providers.Singleton(InfrastructureSettings)
    
    # 외부에서 주입받을 의존성들
    session_factory = providers.Dependency()
    
    # 인프라 서비스들
    uow = providers.Factory(
        SqlAlchemyUnitOfWork, 
        session_factory=session_factory
        )

    hasher = providers.Singleton(Argon2PasswordHasher)

    email_sender = providers.Singleton(SendWelcomeEmailTask, settings=settings)

    jwt_provider = providers.Singleton(
        JwtProvider,
        secret_key=settings.provided.SECRET_KEY,
        algorithm=settings.provided.ALGORITHM,
        access_token_expire_minutes=settings.provided.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

    celery_app = providers.Factory(
        create_celery_app,
        broker=os.getenv("CELERY_BROKER_URL"),
        backend=os.getenv("CELERY_BACKEND_URL"),
        email_task=email_sender,
        broker_connection_retry_on_startup=os.getenv("BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() == "true",
    )
