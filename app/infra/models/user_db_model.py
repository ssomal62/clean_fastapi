from datetime import datetime
from sqlalchemy import String, DateTime, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.domain.user import Role

class UserModel(Base):
    __tablename__ = "User"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    memo: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    role: Mapped[Role] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)