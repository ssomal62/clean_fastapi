from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from app.container.main_container import MainContainer
from app.container.interface_container import InterfaceContainer
from app.container.application_container import ApplicationContainer
from app.container.infrastructure_container import InfrastructureContainer
# user_controller는 이제 container에서 가져옴

import inspect

# 의존성 주입을 위한 컨테이너 생성
infrastructure = InfrastructureContainer()
application = ApplicationContainer()
application.infrastructure.override(infrastructure)

interface = InterfaceContainer()
interface.application.override(application)

# MainContainer에 의존성 주입
container = MainContainer()
container.note_controller.override(interface.note_controller)
container.auth_controller.override(interface.auth_controller)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 컨테이너 초기화
    container.wire(modules=["app.interfaces.user_controller"])
    
    init_res = container.init_resources()
    if inspect.isawaitable(init_res):
        await init_res

    app.include_router(container.user_controller())
    app.include_router(container.auth_controller().router)
    app.include_router(container.note_controller().router)

    yield

    shut_res = container.shutdown_resources()
    if inspect.isawaitable(shut_res):
        await shut_res
    container.unwire()

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    @app.get("/")
    def hello():
        return {"Hello" : "FastAPI"}

    # Pydantic 검증 실패 → 400으로 응답
    @app.exception_handler(RequestValidationError)
    async def validation_exeption_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(status_code=400, content=exc.errors())

    return app

app = create_app()