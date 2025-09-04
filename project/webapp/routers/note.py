from typing import Optional

from fastapi import APIRouter, Depends, Query, Response

from ...src.note.service import NoteService
from ..dtos import CreateNoteBody, UpdateNoteBody, NotePageResponse, NoteResponse
from ...src.note.cqrs.commands import CreateNoteCommand, DeleteNoteCommand, UpdateNoteCommand
from ...src.note.cqrs.queries import GetNoteQuery, GetNotesByTagQuery, GetNotesQuery
from ...src.infrastructure.jwt_provider import CurrentUser, get_current_user_from_token
from ..common.pagination import parse_cursor
from dependency_injector.wiring import Provide, inject
from ..container import MainContainer
from .mapper import note_to_response, notes_to_response

# 라우터 생성
router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "",
    response_model=NoteResponse,
    status_code=201,
    summary="노트 생성",
    description="노트를 생성합니다.",
)
@inject
async def create_note(
    body: CreateNoteBody,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    cmd = CreateNoteCommand.from_request(current_user.id, body)
    note = await note_service.create_note(cmd)
    return note_to_response(note)

@router.get(
    "",
    response_model=NotePageResponse,
    status_code=200,
    summary="노트 목록 조회",
    description="노트 목록을 조회합니다.",
)
@inject
async def get_notes(
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    cursor_created_at, cursor_id = parse_cursor(cursor)

    query = GetNotesQuery.from_request(
        current_user.id, 
        limit, 
        cursor_created_at, 
        cursor_id
    )
    notes, next_cursor = await note_service.get_notes(query)
    return notes_to_response(notes, next_cursor)

@router.get(
    "/{id}",
    response_model=NoteResponse,
    status_code=200,
    summary="노트 상세 조회",
    description="노트를 상세 조회합니다.",
)
@inject
async def get_note(
    id: str,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    query = GetNoteQuery.from_request(current_user.id, id)
    note = await note_service.get_note(query)
    return note_to_response(note)

@router.put(
    "/{id}",
    response_model=NoteResponse,
    status_code=200,
    summary="노트 수정",
    description="노트를 수정합니다.",
)
@inject
async def update_note(
    id: str,
    body: UpdateNoteBody,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    cmd = UpdateNoteCommand.from_request(current_user.id, id, body)
    note = await note_service.update_note(cmd)
    return note_to_response(note)

@router.delete(
    "/{id}",
    status_code=204,
    summary="노트 삭제",
    description="노트를 삭제합니다.",
)
@inject
async def delete_note(
    id: str,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    cmd = DeleteNoteCommand.from_request(current_user.id, id)
    await note_service.delete_note(cmd)
    return Response(status_code=204)

@router.get(
    "/tags/{tag_name}/notes",
    response_model=NotePageResponse,
    status_code=200,
    summary="태그별 노트 목록 조회",
    description="태그별 노트 목록을 조회합니다.",
)
@inject
async def get_notes_by_tag(
    tag_name: str,
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    note_service: NoteService = Depends(Provide[MainContainer.note_service]),
):
    cursor_created_at, cursor_id = parse_cursor(cursor)

    query = GetNotesByTagQuery.from_request(
        current_user.id, 
        tag_name, 
        limit, 
        cursor_created_at, 
        cursor_id
    )
    notes, next_cursor = await note_service.get_notes_by_tag(query)
    return notes_to_response(notes, next_cursor)

