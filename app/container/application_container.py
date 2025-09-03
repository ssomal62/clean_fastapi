from dependency_injector import containers, providers
from app.application.services.note_service import NoteService
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.container.infrastructure_container import InfrastructureContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """애플리케이션 계층 컨테이너 - 비즈니스 로직 서비스들"""
    
    # 인프라 계층 의존성 주입
    infrastructure = providers.DependenciesContainer()
    
    # 애플리케이션 서비스들
    note_service = providers.Factory(NoteService, uow=infrastructure.uow)
    auth_service = providers.Factory(AuthService, uow=infrastructure.uow, hasher=infrastructure.hasher)
    user_service = providers.Factory(
        UserService, 
        uow=infrastructure.uow, 
        hasher=infrastructure.hasher, 
        email_sender=infrastructure.email_sender
    )
