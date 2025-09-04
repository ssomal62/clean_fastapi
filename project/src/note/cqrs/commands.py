from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel

from ..domains import Note, Tag


class CreateNoteCommand(BaseModel):
    user_id: str
    title: str
    content: str
    memo_date: str
    tag_names: Optional[list[str]] | None = None

class UpdateNoteCommand(BaseModel):
    user_id: str
    id: str
    title: Optional[str] | None = None
    content: Optional[str] | None = None
    memo_date: Optional[str] | None = None
    tag_names: Optional[list[str]] | None = None

class DeleteNoteCommand(BaseModel):
    user_id: str
    id: str