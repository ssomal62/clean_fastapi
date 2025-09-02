from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Optional
from app.domain.note import Note, Tag
from app.schemas.note_request import CreateNoteBody, UpdateNoteBody

class CreateNoteCommand(BaseModel):
    user_id: str
    title: str
    content: str
    memo_date: str
    tag_names: Optional[list[str]] | None = None

    @classmethod
    def from_request(cls, user_id: str, body: CreateNoteBody) -> CreateNoteCommand:
        return cls(
            user_id=user_id,
            title=body.title,
            content=body.content,
            memo_date=body.memo_date,
            tag_names=body.tag_names,
        )

class UpdateNoteCommand(BaseModel):
    user_id: str
    id: str
    title: Optional[str] | None = None
    content: Optional[str] | None = None
    memo_date: Optional[str] | None = None
    tag_names: Optional[list[str]] | None = None

    @classmethod
    def from_request(cls, user_id: str, id: str, body: UpdateNoteBody) -> UpdateNoteCommand:
        return cls(
            user_id=user_id,
            id=id,
            title=body.title,
            content=body.content,
            memo_date=body.memo_date,
            tag_names=body.tag_names,
        )

class DeleteNoteCommand(BaseModel):
    user_id: str
    id: str

    @classmethod
    def from_request(cls, user_id: str, id: str) -> DeleteNoteCommand:
        return cls(
            user_id=user_id,
            id=id,
        )