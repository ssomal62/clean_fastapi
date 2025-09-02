from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from app.domain.note import Note
from typing import Optional

class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    memo_date: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, note: Note) -> NoteResponse:
        return cls(
            id=note.id,
            user_id=note.user_id,
            title=note.title,
            content=note.content,
            memo_date=note.memo_date,
            tags=[tag.name for tag in note.tags],
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    @classmethod
    def list_from_domain(cls, notes: list[Note]) -> list[NoteResponse]:
        return [cls.from_domain(note) for note in notes]

class NotePageResponse(BaseModel):
    notes: list[NoteResponse]
    next_cursor: Optional[str] = None