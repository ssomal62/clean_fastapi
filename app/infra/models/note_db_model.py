from datetime import datetime
from sqlalchemy import String, DateTime, TEXT, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

note_tag = Table(
    "note_tag",
    Base.metadata,
    Column("note_id", String(36), ForeignKey("note.id"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tag.id"), primary_key=True),
)

class Note(Base):
    __tablename__ = "note"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(TEXT, nullable=False)
    memo_date: Mapped[str] = mapped_column(String(8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    tags: Mapped[list["Tag"]] = relationship("Tag", secondary="note_tag", back_populates="notes")


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    notes: Mapped[list["Note"]] = relationship("Note", secondary="note_tag", back_populates="tags")