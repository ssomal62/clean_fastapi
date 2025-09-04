from datetime import datetime
from typing import Optional

from sqlalchemy import select, tuple_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import ConflictException, DatabaseException
from .domains import Profile, User
from .entities import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, user: User) -> User:
        try:
            user_model = UserModel(
                id=user.id,
                name=user.profile.name,
                email=user.profile.email,
                password=user.password,
                memo=user.memo,
                role=user.role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            self.session.add(user_model)
            self.session.flush()

            return user
        except IntegrityError as e:
            if "email" in str(e).lower():
                raise ConflictException(
                    f"User with email {user.profile.email} already exists",
                    details={"email": user.profile.email, "error_type": "IntegrityError"}
                )
            raise DatabaseException(
                "Failed to save user",
                details={"error_type": "IntegrityError", "error_message": str(e)}
            )
        except SQLAlchemyError as e:
            raise DatabaseException(
                "Database operation failed",
                details={"error_type": type(e).__name__, "error_message": str(e)}
            )

    async def get_users_page(
        self,
        limit: int,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[str] = None,
        ) -> list[User]:
        stmt = select(UserModel).order_by(
            UserModel.created_at.desc(),
            UserModel.id.desc()
        ).limit(limit)

        if cursor_created_at and cursor_id:
            stmt = stmt.where(
                tuple_(UserModel.created_at, UserModel.id) <
                (cursor_created_at, cursor_id)
            )

        result = await self.session.execute(stmt)
        user_models = result.scalars().all()
        return [to_domain(u) for u in user_models]

    async def find_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        user_model = result.scalar_one_or_none()

        if user_model is None:
            return None

        return User(
            id=user_model.id,
            profile=Profile(name=user_model.name, email=user_model.email),
            password=user_model.password,
            memo=user_model.memo,
            role=user_model.role,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )

    async def update(self, user_id: str, changes: dict) -> User:
            result = await self.session.execute(
                select(UserModel).where(UserModel.id == user_id)
            )

            user_model = result.scalar_one_or_none()
            if not user_model:
                return None

            for key, value in changes.items():
                setattr(user_model, key, value)

            await self.session.flush()
            await self.session.refresh(user_model)

            return User(
                id=user_model.id,
                profile=Profile(name=user_model.name, email=user_model.email),
                password=user_model.password,
                memo=user_model.memo,
                role=user_model.role,
                created_at=user_model.created_at,
                updated_at=user_model.updated_at,
            )

    async def delete(self, user_id: str) -> bool:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return False
        
        await self.session.delete(user_model)
        return True

def to_domain(user_model: UserModel) -> User:
    """UserModel → User 도메인 객체 변환"""
    return User(
        id=user_model.id,
        profile=Profile(name=user_model.name, email=user_model.email),
        password=user_model.password,
        memo=user_model.memo,
        role=user_model.role,
        created_at=user_model.created_at,
        updated_at=user_model.updated_at,
    )