from __future__ import annotations

from project.src.user.domains import User
from project.src.note.domains import Note
from ..dtos import UserResponse, NoteResponse, NotePageResponse, UserPageResponse, CreateNoteBody, UpdateNoteBody
from project.src.note.cqrs.commands import CreateNoteCommand, UpdateNoteCommand, DeleteNoteCommand
from project.src.note.cqrs.queries import GetNotesQuery, GetNoteQuery, GetNotesByTagQuery
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

# DTO to Command/Query 변환 함수들
def to_create_command(user_id: str, body: CreateNoteBody) -> CreateNoteCommand:
    """CreateNoteBody를 CreateNoteCommand로 변환"""
    return CreateNoteCommand(
        user_id=user_id,
        title=body.title,
        content=body.content,
        memo_date=body.memo_date,
        tag_names=body.tag_names,
    )

def to_update_command(user_id: str, note_id: str, body: UpdateNoteBody) -> UpdateNoteCommand:
    """UpdateNoteBody를 UpdateNoteCommand로 변환"""
    return UpdateNoteCommand(
        user_id=user_id,
        id=note_id,
        title=body.title,
        content=body.content,
        memo_date=body.memo_date,
        tag_names=body.tag_names,
    )

def to_delete_command(user_id: str, note_id: str) -> DeleteNoteCommand:
    """파라미터를 DeleteNoteCommand로 변환"""
    return DeleteNoteCommand(
        user_id=user_id,
        id=note_id,
    )

def to_get_notes_query(
    user_id: str, 
    limit: int, 
    cursor_created_at=None, 
    cursor_id=None
) -> GetNotesQuery:
    """파라미터를 GetNotesQuery로 변환"""
    return GetNotesQuery(
        user_id=user_id,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )

def to_get_note_query(user_id: str, note_id: str) -> GetNoteQuery:
    """파라미터를 GetNoteQuery로 변환"""
    return GetNoteQuery(
        user_id=user_id,
        id=note_id,
    )

def to_get_notes_by_tag_query(
    user_id: str, 
    tag_name: str, 
    limit: int, 
    cursor_created_at=None, 
    cursor_id=None
) -> GetNotesByTagQuery:
    """파라미터를 GetNotesByTagQuery로 변환"""
    return GetNotesByTagQuery(
        user_id=user_id,
        tag_name=tag_name,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )