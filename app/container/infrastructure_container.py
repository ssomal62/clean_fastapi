from dependency_injector import containers, providers
from app.infra.unit_of_work import SqlAlchemyUnitOfWork
from app.database import get_async_sessionmaker
from app.infra.adapters.argon2_password_hasher import Argon2PasswordHasher
from app.infra.adapters.celery_email_sander import CeleryEmailSender
from app.core.config import Settings


class InfrastructureContainer(containers.DeclarativeContainer):
    """인프라 계층 컨테이너 - 데이터베이스, 외부 서비스 등"""
    
    config = providers.Singleton(Settings)
    session_factory = providers.Factory(get_async_sessionmaker, settings=config)
    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)
    hasher = providers.Singleton(Argon2PasswordHasher)
    email_sender = providers.Singleton(CeleryEmailSender)
