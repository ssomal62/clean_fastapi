from dependency_injector import containers, providers
from app.application.services.note_service import NoteService
from app.application.services.auth_service import AuthService
from app.application.services.user_service import UserService
from app.interfaces.note_controller import NoteController
from app.interfaces.auth_controller import AuthController
from app.infra.unit_of_work import SqlAlchemyUnitOfWork
from app.database import get_async_sessionmaker
from app.infra.adapters.argon2_password_hasher import Argon2PasswordHasher
from app.infra.adapters.celery_email_sander import CeleryEmailSender
from app.core.config import Settings

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration( # @inject를 쓰는경우 wiring_config를 써야함
        modules=[
            "app.interfaces.user_controller",
        ]
    )

    config = providers.Singleton(Settings)
    session_factory = providers.Factory(get_async_sessionmaker, settings=config) 
    uow = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)
    hasher = providers.Singleton(Argon2PasswordHasher)
    email_sender = providers.Singleton(CeleryEmailSender)

    note_service = providers.Factory(NoteService, uow=uow)
    auth_service = providers.Factory(AuthService, uow=uow, hasher=hasher)
    user_service = providers.Factory(UserService, uow=uow, hasher=hasher, email_sender=email_sender)

    note_controller = providers.Factory(NoteController, note_service=note_service)
    auth_controller = providers.Factory(AuthController, auth_service=auth_service)