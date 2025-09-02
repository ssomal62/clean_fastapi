import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi.exceptions import HTTPException
from app.domain.note import Note, Tag
from app.application.unit_of_work import UnitOfWork
from app.application.commands.note_commands import CreateNoteCommand, UpdateNoteCommand, DeleteNoteCommand
from app.application.queries.note_queries import GetNotesQuery, GetNoteQuery, GetNotesByTagQuery

class NoteService:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def get_notes(self, query: GetNotesQuery) -> tuple[list[Note], Optional[str]]:
        async with self.uow as uow:
            notes = await uow.note_repository.get_notes(
                query.user_id, query.limit, query.cursor_created_at, query.cursor_id
                )

            if notes:
                last_note = notes[-1]
                next_cursor = f"{last_note.created_at.isoformat()}_{last_note.id}"
            else:
                next_cursor = None

            return notes, next_cursor

    async def get_note(self, query: GetNoteQuery) -> Note:
        async with self.uow as uow:

            note = await uow.note_repository.find_by_id(query.user_id, query.id)
            if not note:
                raise HTTPException(status_code=404, detail="Note not found")
                
            return note

    async def create_note(self, cmd: CreateNoteCommand) -> Note:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        async with self.uow as uow:
            tags = [
                Tag(
                    id=str(uuid.uuid4()),
                    name=name,
                    updated_at=now,
                    created_at=now,
                )
                for name in (cmd.tag_names or [])
            ]

            note: Note = Note(
                id=str(uuid.uuid4()),
                user_id=cmd.user_id,
                title=cmd.title,
                content=cmd.content,
                memo_date=cmd.memo_date,
                tags=tags,
                created_at=now,
                updated_at=now,
            )

            await uow.note_repository.save(cmd.user_id, note)
            return note

    async def update_note(self, cmd: UpdateNoteCommand) -> Note:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        async with self.uow as uow:
            note = await uow.note_repository.find_by_id(cmd.user_id, cmd.id)

            if not note:
                raise HTTPException(status_code=404, detail="Note not found")

            if cmd.title is not None:
                note.change_title(cmd.title)
            if cmd.content is not None:
                note.change_content(cmd.content)
            if cmd.memo_date is not None:
                note.change_memo_date(cmd.memo_date)
            if cmd.tag_names is not None:
                tags = [
                    Tag(
                        id=str(uuid.uuid4()),
                        name=name,
                        created_at=now,
                        updated_at=now,
                    )
                    for name in (cmd.tag_names or [])
                ]
                note.change_tags(tags)

            note.updated_at = now
            
            # save
            # 서비스 계층에서는 엔티티를 꺼내 변경 후 다시 저장
            # ORM은 더티 체킹을 통해 어떤 필드가 바뀌었는지 알아서 추적하고 UPDATE SQL을 생성
            # 그래서 save(entity) 하나로 통일
            await uow.note_repository.save(cmd.user_id, note)
            return note

    async def delete_note(self, cmd: DeleteNoteCommand) -> bool:
        async with self.uow as uow:
            note = await uow.note_repository.find_by_id(cmd.user_id, cmd.id)
            if not note:
                raise HTTPException(status_code=404, detail="Note not found")
                
            note.remove_all_tags()
            result = await uow.note_repository.delete(note)
            return result

    async def get_notes_by_tag(self, query: GetNotesByTagQuery) -> tuple[list[Note], Optional[str]]:
        async with self.uow as uow:
            notes = await uow.note_repository.get_notes_by_tag_name(
            query.user_id, query.tag_name, query.limit, query.cursor_created_at, query.cursor_id
            )

            if notes:
                last_note = notes[-1]
                next_cursor = f"{last_note.created_at.isoformat()}_{last_note.id}"
            else:
                next_cursor = None

            return notes, next_cursor