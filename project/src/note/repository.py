from datetime import datetime
from typing import Optional

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .domains import Note, Tag
from .entities import Note as NoteModel, Tag as TagModel


class SqlAlchemyNoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_notes(
        self, 
        user_id: str, 
        limit: int, 
        cursor_created_at: Optional[datetime] = None, 
        cursor_id: Optional[str] = None
        ) -> list[Note]:
        stmt = (
            select(NoteModel)
            .where(NoteModel.user_id == user_id)
            .options(selectinload(NoteModel.tags))
            .order_by(NoteModel.created_at.desc(), NoteModel.id.desc())
            .limit(limit)
        )

        if cursor_created_at and cursor_id:
            stmt = stmt.where(
                tuple_(NoteModel.created_at, NoteModel.id) <
                (cursor_created_at, cursor_id)
            )

        result = await self.session.execute(stmt)
        note_models = result.scalars().all()
        return [to_domain(n) for n in note_models]
        
    async def find_by_id(self, user_id: str, id: str) -> Note:
        stmt = (
            select(NoteModel)
            .where(NoteModel.user_id == user_id, NoteModel.id == id)
            .options(selectinload(NoteModel.tags))
        )

        result = await self.session.execute(stmt)
        note_model = result.scalar_one_or_none()
        if not note_model:
            return None
        return to_domain(note_model)

    # ---- 생성/업데이트(UPSERT 유사) ----
    # 트랜잭션은 UoW가 관리하므로 여기서 begin()/commit() 하지 않음.
    async def save(self, user_id: str, note: Note) -> Note:
        # 1. 기존 노트 로드 (+태그)
        stmt = (
            select(NoteModel)
            .where(NoteModel.id == note.id, NoteModel.user_id == user_id)
            .options(selectinload(NoteModel.tags))
        )
        result = await self.session.execute(stmt)
        note_model = result.scalar_one_or_none()

        if not note_model:
            # 2. 새 노트 생성  -> NoteModel로 변환 후 add
            note_model = NoteModel(
                id=note.id,
                user_id=note.user_id,
                title=note.title,
                content=note.content,
                memo_date=note.memo_date,
                created_at=note.created_at,
                updated_at=note.updated_at,
            )
            self.session.add(note_model)

        else:
            # 3. 기존 노트 업데이트 -> 필드 값 업데이트
            # 이미 세션에서 로드된 엔티티(persistent)이므로
            # 변경 사항은 SQLAlchemy 더티체킹으로 추적됨.
            # → commit() 시점에 UPDATE SQL 자동 실행, session.add() 필요 없음.
            note_model.title = note.title
            note_model.content = note.content
            note_model.memo_date = note.memo_date
            note_model.updated_at = note.updated_at

        # 4.태그 처리 (중복 방지)
        tag_models = []
        if note.tags:
            tag_names = [tag.name for tag in note.tags]
            stmt = select(TagModel).where(TagModel.name.in_(tag_names))
            result = await self.session.execute(stmt)
            existing_tag = {t.name: t for t in result.scalars().all()}

            for tag in note.tags:
                tag_model = existing_tag.get(tag.name)
                if not tag_model:
                    tag_model = TagModel(
                        id=tag.id,
                        name=tag.name,
                        created_at=tag.created_at,
                        updated_at=tag.updated_at
                    )
                    self.session.add(tag_model)
                tag_models.append(tag_model)
        
        # 관계는 최종 상태로 "할당" (clear/extend 대신)
        note_model.tags = tag_models
        return note

    async def delete(self, note: Note) -> bool:
        # 가능한 DB에서 로드해서 삭제하는 쪽이 명확 
        stmt = select(NoteModel).where(
            NoteModel.id == note.id,
            NoteModel.user_id == note.user_id,
        )
        result = await self.session.execute(stmt)
        note_model = result.scalar_one_or_none()
        if not note_model:
            return False

        await self.session.delete(note_model)
        # 커밋은 UoW가 책임짐
        return True

    async def delete_tags(self, user_id: str, id: str) -> bool: 
        stmt = (
            select(NoteModel)
            .where(NoteModel.user_id == user_id, NoteModel.id == id)
            .options(selectinload(NoteModel.tags))
        )
        result = await self.session.execute(stmt)
        note_model = result.scalar_one_or_none()
        if not note_model:
            return False

        note_model.tags = []  # 관계 초기화
        return True

    async def get_notes_by_tag_name(
        self, 
        user_id: str, 
        tag_name: str, 
        limit: int, 
        cursor_created_at: Optional[datetime] = None, 
        cursor_id: Optional[str] = None
        ) -> list[Note]:
        stmt = (
            select(NoteModel)
            .where(
                NoteModel.user_id == user_id,
                NoteModel.tags.any(TagModel.name == tag_name),  # many-to-many 필터
            )
            .options(selectinload(NoteModel.tags))
            .order_by(NoteModel.created_at.desc(), NoteModel.id.desc())
            .limit(limit)
        )

        if cursor_created_at and cursor_id:
            stmt = stmt.where(
                tuple_(NoteModel.created_at, NoteModel.id) < (cursor_created_at, cursor_id)
            )

        result = await self.session.execute(stmt)
        note_models = result.scalars().all()
        return [to_domain(n) for n in note_models]

def to_domain(note_model: NoteModel) -> Note:
    return Note(
        id=note_model.id,
        user_id=note_model.user_id,
        title=note_model.title,
        content=note_model.content,
        memo_date=note_model.memo_date,
        tags=[Tag(id=tag.id, name=tag.name, created_at=tag.created_at, updated_at=tag.updated_at) for tag in note_model.tags],
        created_at=note_model.created_at,
        updated_at=note_model.updated_at,
    )