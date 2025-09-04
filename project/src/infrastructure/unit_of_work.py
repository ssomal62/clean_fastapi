from sqlalchemy.ext.asyncio import AsyncSession
from ..database.database import SessionFactory
from typing import Optional, Type
from ..user.repository import SqlAlchemyUserRepository
from ..note.repository import SqlAlchemyNoteRepository


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.user_repository: Optional[SqlAlchemyUserRepository] = None
        self.note_repository: Optional[SqlAlchemyNoteRepository] = None

    async def __aenter__(self):
        async_sessionmaker = self._session_factory.get_async_sessionmaker()
        self.session = async_sessionmaker()

        # 트랜잭션 시작
        await self.session.begin()

        # 리포지토리들을 세션에 바인딩
        self.user_repository = SqlAlchemyUserRepository(self.session)
        self.note_repository = SqlAlchemyNoteRepository(self.session)

        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()


# UnitOfWork 별칭
UnitOfWork = SqlAlchemyUnitOfWork
