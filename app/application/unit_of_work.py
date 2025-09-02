from typing import Protocol
from typing import Optional, Type, Any

class UnitOfWork(Protocol):

    note_repository: Any
    user_repository: Any

    async def __aenter__(self): ...

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc, tb): ...

    async def commit(self): ...

    async def rollback(self): ...