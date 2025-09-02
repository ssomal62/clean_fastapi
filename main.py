from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from app.container import Container
from app.interfaces.user_controller import router as user_router

import inspect

container = Container()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_res = container.init_resources()
    if inspect.isawaitable(init_res):
        await init_res

    app.include_router(user_router)
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