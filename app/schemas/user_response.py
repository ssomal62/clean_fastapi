from __future__ import annotations
from pydantic import BaseModel
from datetime import datetime
from app.domain.user import User

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    memo: str | None
    updated_at: datetime

    # 변환 함수
    @classmethod
    def from_domain(cls, user: User) -> UserResponse:
        return cls(
            id=user.id,
            name=user.profile.name,
            email=user.profile.email,
            memo=user.memo,
            updated_at=user.updated_at,
        )

    @classmethod
    def list_from_domain(cls, users: list[User]) -> list[UserResponse]:
        return [cls.from_domain(u) for u in users]