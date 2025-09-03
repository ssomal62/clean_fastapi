from dependency_injector import containers, providers
from app.container.infrastructure_container import InfrastructureContainer
from app.container.application_container import ApplicationContainer
from app.container.interface_container import InterfaceContainer


class MainContainer(containers.DeclarativeContainer):
    """메인 컨테이너 - 모든 계층을 조합하는 최상위 컨테이너"""

    wiring_config = containers.WiringConfiguration(
        modules=["app.interfaces.user_controller"]
    )
    
    # 각 계층 컨테이너들
    infrastructure = providers.Container(InfrastructureContainer)
    application = providers.Container(ApplicationContainer, infrastructure=infrastructure)
    interface = providers.Container(InterfaceContainer, application=application)