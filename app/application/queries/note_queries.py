from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class GetNotesQuery(BaseModel):
    user_id: str
    limit: int
    cursor_created_at: Optional[datetime] | None = None
    cursor_id: Optional[str] | None = None

    @classmethod
    def from_request(
        cls, 
        user_id: str, 
        limit: int, 
        cursor_created_at: Optional[datetime] | None = None, 
        cursor_id: Optional[str] | None = None
        ) -> GetNotesQuery:
        return cls(
            user_id=user_id,
            limit=limit,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
        )

class GetNoteQuery(BaseModel):
    user_id: str
    id: str

    @classmethod
    def from_request(cls, user_id: str, id: str) -> GetNoteQuery:
        return cls(
            user_id=user_id,
            id=id,
        )

class GetNotesByTagQuery(BaseModel):
    user_id: str
    tag_name: str
    limit: int
    cursor_created_at: Optional[datetime] | None = None
    cursor_id: Optional[str] | None = None

    @classmethod
    def from_request(
        cls, 
        user_id: str, 
        tag_name: str, 
        limit: int, 
        cursor_created_at: Optional[datetime] | None = None, 
        cursor_id: Optional[str] | None = None
        ) -> GetNotesByTagQuery:
        return cls(
            user_id=user_id,
            tag_name=tag_name,
            limit=limit,
            cursor_created_at=cursor_created_at,
            cursor_id=cursor_id,
        )