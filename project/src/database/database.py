from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .settings import DatabaseSettings

# 0. 공용 Base 정의
class Base(DeclarativeBase):
    pass


class SessionFactory:
    """비동기 SQLAlchemy 세션 팩토리"""

    def __init__(self, settings: DatabaseSettings):
        self._engine = create_async_engine(
            settings.POSTGRES_URL,
            echo=settings.DB_ECHO,
            future=True,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )

    def __call__(self) -> AsyncSession:
        """새로운 세션 인스턴스 반환"""
        return self._sessionmaker()

    @property
    def engine(self):
        return self._engine

    @property
    def sessionmaker(self):
        """원본 sessionmaker 접근용"""
        return self._sessionmaker
    
    def get_async_sessionmaker(self):
        """비동기 SQLAlchemy 세션 팩토리 반환"""
        return self._sessionmaker
