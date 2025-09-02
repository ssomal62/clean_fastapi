from typing import Optional
from datetime import datetime
from app.domain.note import Note
from typing import Protocol

class NoteRepository(Protocol):

    async def get_notes(
        self,
        user_id: str,
        limit: int,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[str] = None,
    ) -> list[Note]: ...

    async def find_by_id(self, user_id: str, id: str) -> Note: ...

    async def save(self, user_id: str, note: Note) -> Note: ...

    async def delete(note: Note) -> bool: ...

    async def delete_tags(self, user_id: str, id: str) -> bool: ...

    async def get_notes_by_tag_name(
        self,
        user_id: str,
        tag_name: str,
        limit: int,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[str] = None,
    ) -> list[Note]: ...
    