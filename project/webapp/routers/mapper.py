from __future__ import annotations

from project.src.user.domains import User
from project.src.note.domains import Note
from ..dtos import UserResponse, NoteResponse, NotePageResponse, UserPageResponse
from typing import Optional

def user_to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        name=u.profile.name,
        email=u.profile.email,
        memo=u.memo,
        updated_at=u.updated_at,
    )

def users_to_response(
    users: list[User], 
    next_cursor: Optional[str] = None
    ) -> UserPageResponse:
    return UserPageResponse(
        users=[user_to_response(u) for u in users],
        next_cursor=next_cursor,
    )

def note_to_response(n: Note) -> NoteResponse:
    return NoteResponse(
        id=n.id,
        user_id=n.user_id,
        title=n.title,
        content=n.content,
        memo_date=n.memo_date,
        tags=[t.name for t in n.tags],
        created_at=n.created_at,
        updated_at=n.updated_at,
    )

def notes_to_response(
    notes: list[Note], 
    next_cursor: Optional[str] = None
    ) -> NotePageResponse:
    return NotePageResponse(
        notes=[note_to_response(n) for n in notes],
        next_cursor=next_cursor,
    )