from dependency_injector import containers, providers

from .service import NoteService


class NoteContainer(containers.DeclarativeContainer):
    """Note 도메인 컨테이너"""
    
    uow = providers.Dependency()
    note_service = providers.Factory(NoteService, uow=uow)
