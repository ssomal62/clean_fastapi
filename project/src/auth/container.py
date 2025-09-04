from dependency_injector import containers, providers

from .service import AuthService


class AuthContainer(containers.DeclarativeContainer):
    """Auth 도메인 컨테이너"""
    
    # 외부 의존성 주입
    uow = providers.Dependency()
    hasher = providers.Dependency()
    jwt_provider = providers.Dependency()
    auth_service = providers.Factory(AuthService, uow=uow, hasher=hasher, jwt_provider=jwt_provider)
