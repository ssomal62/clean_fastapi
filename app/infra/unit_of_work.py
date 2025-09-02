from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.infra.repositories.note_repository_sqlalchemy import SqlAlchemyNoteRepository
from app.infra.repositories.user_repository_sqlalchemy import SqlAlchemyUserRepository
from app.application.unit_of_work import UnitOfWork
from typing import Optional, Type

class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.note_repository: Optional[SqlAlchemyNoteRepository] = None
        self.user_repository: Optional[SqlAlchemyUserRepository] = None

    async def __aenter__(self):
        # 세션은 컨텍스트 진입 시점에 생성
        self.session = self._session_factory()

        # 트랜잭션 시작
        await self.session.begin()

        # 세션 바인딩된 리포지토리 생성
        self.note_repository = SqlAlchemyNoteRepository(self.session)
        self.user_repository = SqlAlchemyUserRepository(self.session)

        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()  