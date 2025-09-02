from fastapi import APIRouter, Depends, Query, Response
from app.application.services.note_service import NoteService
from app.schemas.note_response import NoteResponse, NotePageResponse
from app.schemas.note_request import CreateNoteBody, UpdateNoteBody
from app.common.security import CurrentUser, get_current_user
from typing import Optional
from utils.pagination import parse_cursor
from app.application.commands.note_commands import CreateNoteCommand, UpdateNoteCommand, DeleteNoteCommand
from app.application.queries.note_queries import GetNotesQuery, GetNoteQuery, GetNotesByTagQuery
from app.interfaces.base_controller import BaseController

class NoteController(BaseController):
    """노트 도메인 컨트롤러"""

    def __init__(self, note_service: NoteService):
        self.note_service = note_service
        super().__init__()

    def register_routes(self) -> APIRouter:

        router = APIRouter(prefix="/notes", tags=["notes"])

        # ------------------------------
        #   Route Definitions
        # ------------------------------

        router.add_api_route(
            "",
            self.create_note,
            methods=["POST"],
            response_model=NoteResponse,
            status_code=201,
            summary="노트 생성",
            description="노트를 생성합니다.",
        )

        router.add_api_route(
            "",
            self.get_notes,
            methods=["GET"],
            response_model=NotePageResponse,
            status_code=200,
            summary="노트 목록 조회",
            description="노트 목록을 조회합니다.",
        )

        router.add_api_route(
            "/{id}",
            self.get_note,
            methods=["GET"],
            response_model=NoteResponse,
            status_code=200,
            summary="노트 상세 조회",
            description="노트를 상세 조회합니다.",
        )

        router.add_api_route(
            "/{id}",
            self.update_note,
            methods=["PUT"],
            response_model=NoteResponse,
            status_code=200,
            summary="노트 수정",
            description="노트를 수정합니다.",
        )

        router.add_api_route(
            "/{id}",
            self.delete_note,
            methods=["DELETE"],
            status_code=204,
            summary="노트 삭제",
            description="노트를 삭제합니다.",
        )

        router.add_api_route(
            "/tags/{tag_name}/notes",
            self.get_notes_by_tag,
            methods=["GET"],
            response_model=NotePageResponse,
            status_code=200,
            summary="태그별 노트 목록 조회",
            description="태그별 노트 목록을 조회합니다.",
        )

        return router

    # ------------------------------
    #   Route Handlers
    # ------------------------------

    async def create_note(
        self,
        body: CreateNoteBody,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        cmd = CreateNoteCommand.from_request(current_user.id, body)
        note = await self.note_service.create_note(cmd)
        return NoteResponse.from_domain(note)

    async def get_notes(
        self,
        limit: int = Query(default=10, ge=1, le=100),
        cursor: Optional[str] = None,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        cursor_created_at, cursor_id = parse_cursor(cursor)

        query = GetNotesQuery.from_request(
            current_user.id, 
            limit, 
            cursor_created_at, 
            cursor_id
            )
        notes, next_cursor = await self.note_service.get_notes(query)
        return NotePageResponse(
            notes=NoteResponse.list_from_domain(notes), 
            next_cursor=next_cursor
            )

    async def get_note(
        self,
        id: str,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        query = GetNoteQuery.from_request(current_user.id, id)
        note = await self.note_service.get_note(query)
        return NoteResponse.from_domain(note)

    async def update_note(
        self,
        id: str,
        body: UpdateNoteBody,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        cmd = UpdateNoteCommand.from_request(current_user.id, id, body)
        note = await self.note_service.update_note(cmd)
        return NoteResponse.from_domain(note)

    async def delete_note(
        self,
        id: str,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        cmd = DeleteNoteCommand.from_request(current_user.id, id)
        await self.note_service.delete_note(cmd)
        return Response(status_code=204)

    async def get_notes_by_tag(
        self,
        tag_name: str,
        limit: int = Query(default=10, ge=1, le=100),
        cursor: Optional[str] = None,
        current_user: CurrentUser = Depends(get_current_user),
    ):
        cursor_created_at, cursor_id = parse_cursor(cursor)

        query = GetNotesByTagQuery.from_request(
            current_user.id, 
            tag_name, 
            limit, 
            cursor_created_at, 
            cursor_id
            )
        notes, next_cursor = await self.note_service.get_notes_by_tag(query)
        return NotePageResponse(
            notes=NoteResponse.list_from_domain(notes), 
            next_cursor=next_cursor
            )

