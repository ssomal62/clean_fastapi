from dependency_injector import containers, providers
from app.interfaces.note_controller import NoteController
from app.interfaces.auth_controller import AuthController
from app.container.application_container import ApplicationContainer
from app.interfaces import user_controller
 

class InterfaceContainer(containers.DeclarativeContainer):
    """인터페이스 계층 컨테이너 - 컨트롤러들"""

    # 애플리케이션 계층 의존성 주입
    application = providers.DependenciesContainer()
    
    # 컨트롤러들
    note_controller = providers.Factory(NoteController, note_service=application.note_service)
    auth_controller = providers.Factory(AuthController, auth_service=application.auth_service)
    
    # 함수 기반 라우터 (user_controller)
    user_router = providers.Object(user_controller.router)
    