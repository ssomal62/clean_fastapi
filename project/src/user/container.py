from dependency_injector import containers, providers

from .service import UserService


class UserContainer(containers.DeclarativeContainer):
    """User 도메인 컨테이너"""
    
    uow = providers.Dependency()
    hasher = providers.Dependency()
    email_sender = providers.Dependency()
    user_service = providers.Factory(UserService, uow=uow, hasher=hasher, email_sender=email_sender)