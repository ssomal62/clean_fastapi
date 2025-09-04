from dependency_injector import containers, providers

from ..src.database.container import DatabaseContainer
from ..src.infrastructure.container import InfrastructureContainer
from ..src.user.container import UserContainer
from ..src.note.container import NoteContainer
from ..src.auth.container import AuthContainer
from ..src.infrastructure.jwt_provider import get_current_user_from_token, get_admin_user_from_token

class MainContainer(containers.DeclarativeContainer):

    database = providers.Container(DatabaseContainer)

    infrastructure = providers.Container(
        InfrastructureContainer, 
        session_factory=database.session_factory
        ) 

    jwt_provider = infrastructure.jwt_provider
    
    # JWT 관련 함수들 노출
    get_current_user = providers.Callable(get_current_user_from_token)
    get_admin_user = providers.Callable(get_admin_user_from_token)

    user = providers.Container(
        UserContainer, 
        uow=infrastructure.uow, 
        hasher=infrastructure.hasher, 
        jwt_provider=infrastructure.jwt_provider,
        email_sender=infrastructure.email_sender
        )
    

    user_service = user.user_service

    note = providers.Container(
        NoteContainer, 
        uow=infrastructure.uow
        )
    

    note_service = note.note_service

    auth = providers.Container(
        AuthContainer, 
        uow=infrastructure.uow, 
        hasher=infrastructure.hasher, 
        jwt_provider=infrastructure.jwt_provider)
    

    auth_service = auth.auth_service