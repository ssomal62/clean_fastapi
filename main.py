from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from app.container.main_container import MainContainer

import inspect

# 최상위 컨테이너
container = MainContainer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 컨테이너 초기화
    container.wire(modules=["app.interfaces.user_controller"])
    
    init_res = container.init_resources()
    if inspect.isawaitable(init_res):
        await init_res

    app.include_router(container.interface().user_router())
    app.include_router(container.interface().auth_controller().router)
    app.include_router(container.interface().note_controller().router)

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