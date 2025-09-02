from dependency_injector import containers, providers
from app.application.services.note_service import NoteService
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.interfaces.note_controller import NoteController
from app.interfaces.auth_controller import AuthController
from app.infra.unit_of_work import SqlAlchemyUnitOfWork
from app.database import get_async_sessionmaker

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration( # @inject를 쓰는경우 wiring_config를 써야함
        modules=[
            "app.interfaces.user_controller",
        ]
    )

    session_factory = providers.Factory(get_async_sessionmaker) 
    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    note_service = providers.Factory(NoteService, uow=uow)
    auth_service = providers.Factory(AuthService, uow=uow)
    user_service = providers.Factory(UserService, uow=uow)

    note_controller = providers.Factory(NoteController, note_service=note_service)
    auth_controller = providers.Factory(AuthController, auth_service=auth_service)