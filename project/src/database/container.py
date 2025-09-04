from dependency_injector import containers, providers

from .database import SessionFactory
from .settings import DatabaseSettings


class DatabaseContainer(containers.DeclarativeContainer):
    """Database 도메인 컨테이너"""

    settings = providers.Singleton(DatabaseSettings)
    session_factory = providers.Factory(SessionFactory,settings=settings)