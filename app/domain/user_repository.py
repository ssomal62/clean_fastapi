from typing import Protocol, Optional
from sqlalchemy import Boolean
from app.domain.user import User
from datetime import datetime
from typing import Optional

class UserRepository(Protocol):
    
    async def save(self, user: User) -> User: ... 

    async def get_users_page(self, limit: int, cursor_created_at: Optional[datetime] = None, cursor_id: Optional[str] = None) -> list[User]: ...

    async def find_by_email(self, email: str) -> Optional[User]: ...

    async def update(self, user_id: str, changes: dict) -> User: ...    

    async def delete(self, user_id: str) -> bool: ...
