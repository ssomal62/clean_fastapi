from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GetNotesQuery(BaseModel):
    user_id: str
    limit: int
    cursor_created_at: Optional[datetime] | None = None
    cursor_id: Optional[str] | None = None

class GetNoteQuery(BaseModel):
    user_id: str
    id: str

class GetNotesByTagQuery(BaseModel):
    user_id: str
    tag_name: str
    limit: int
    cursor_created_at: Optional[datetime] | None = None
    cursor_id: Optional[str] | None = None