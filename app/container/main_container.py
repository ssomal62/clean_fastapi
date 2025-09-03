from dependency_injector import containers, providers
from app.container.infrastructure_container import InfrastructureContainer
from app.container.application_container import ApplicationContainer
from app.container.interface_container import InterfaceContainer


class MainContainer(containers.DeclarativeContainer):
    """메인 컨테이너 - 모든 계층을 조합하는 최상위 컨테이너"""
    
    # 각 계층 컨테이너들
    infrastructure = providers.Container(InfrastructureContainer)
    application = providers.Container(ApplicationContainer, infrastructure=infrastructure)
    interface = providers.Container(InterfaceContainer, application=application)
    
    # 컨트롤러들을 의존성으로 주입받음 (올바른 의존성 주입)
    note_controller = providers.Dependency()
    auth_controller = providers.Dependency()
    
    # UserController는 함수 기반 라우터이므로 router를 반환
    user_controller = providers.Factory(lambda: __import__('app.interfaces.user_controller', fromlist=['router']).router)
