import inspect
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .container import MainContainer
from ..webapp.routers.user import router as user_router
from ..webapp.routers.note import router as note_router
from ..webapp.routers.auth import router as auth_router
from ..webapp.routers.health import router as health_router
from .common.setup_middleware import setup_middleware


container = MainContainer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Resources 쓴 경우에만 init/shutdown (없으면 통째로 생략해도 됨)
    init_res = container.init_resources()
    if inspect.isawaitable(init_res):
        await init_res
    try:
        yield
    finally:
        shut_res = container.shutdown_resources()
        if inspect.isawaitable(shut_res):
            await shut_res

def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)

    # 컨테이너를 앱에 등록
    app.container = container
    
    container.wire(modules=[
        "project.webapp.routers.user",
        "project.webapp.routers.note", 
        "project.webapp.routers.auth"
    ])
    
    setup_middleware(app)

    app.include_router(health_router)
    app.include_router(user_router)
    app.include_router(note_router)
    app.include_router(auth_router)

    @app.get("/")
    async def root():
        return {
            "message": "Clean FastAPI - TIL API",
            "version": "0.1.0",
            "endpoints": {"health": "/health", "docs": "/docs", "auth": "/auth", "users": "/users", "notes": "/notes"},
            "status": "running",
        }

    return app

app = create_app()