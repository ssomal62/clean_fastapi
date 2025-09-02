from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from fastapi import Request
from typing import AsyncGenerator
from app.core.config import settings
from sqlalchemy.orm import declarative_base

# 0. 공용 Base 정의 (모든 모델이 이걸 상속)
Base = declarative_base()

def get_async_sessionmaker():
    engine = create_async_engine(settings.postgres_url, echo=True, future=True)

    return async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
    )
