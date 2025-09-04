# 1. 표준 라이브러리
import uuid
from datetime import datetime, timezone
# 2. 서드파티 라이브러리 (pip install 같이 외부에서 설치해야하는 라이브러리)
# 3. 타입힌트
from typing import Optional

from ..infrastructure.email_sender import SendWelcomeEmailTask as EmailSender
from ..infrastructure.argon2_password_hasher import Argon2PasswordHasher as PasswordHasher
from ..infrastructure.unit_of_work import SqlAlchemyUnitOfWork as UnitOfWork
# 4. 로컬 패키지
from ..shared.exceptions import (ConflictException, NotFoundException,
                                   UnauthorizedException)
from .domains import Profile, User


class UserService:

    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, email_sender: EmailSender):
        self.uow = uow
        self.hasher = hasher
        self.email_sender = email_sender

    # ---------------------------------------------------------------------
    # Create
    # ---------------------------------------------------------------------

    async def create_user(self, name: str, email: str, password: str, memo: str | None = None, role: str = "user") -> User:
        async with self.uow as uow:
            exists_user = await self.find_user_by_email(email)
            if exists_user: 
                raise ConflictException(f"User already exists: {email}", details={"email": email})

            now = datetime.now(timezone.utc).replace(tzinfo=None)

            user: User = User(
                id=str(uuid.uuid4()),
                profile=Profile(name=name, email=email),
                password=self.hasher.encrypt(password),
                memo=memo,
                role=role,
                created_at=now,
                updated_at=now,
            )
            await uow.user_repository.save(user)

            # 임시로 이메일 발송 비활성화
            # await self.email_sender.send(
            #     email, 
            #     "Clean-Fastapi 회원가입 완료",
            #     f"{name}님, 회원가입을 환영합니다!",
            #     )
            return user

    # ---------------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------------

    async def list_users(
        self,
        limit: int,
        cursor_created_at: Optional[datetime] = None,
        cursor_id: Optional[str] = None,
        ):
        async with self.uow as uow:
            users = await uow.user_repository.get_users_page(limit, cursor_created_at, cursor_id)

            #next_cursor = 마지막 유저 값 조합
            next_cursor = None
            if users:
                last_user = users[-1]
                next_cursor = f"{last_user.created_at.isoformat()}_{last_user.id}"
            return users, next_cursor

    async def find_user_by_email(self, email: str) -> Optional[User]:
        async with self.uow as uow:
            return await uow.user_repository.find_by_email(email)

    # ---------------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------------

    async def update_user(
        self, 
        email: str, 
        current_password: str, 
        new_password: str | None,
        new_name: str | None = None, 
        new_memo: str | None = None,
        new_role: str | None = None,
        ) -> User:
        async with self.uow as uow:
            user = await self.find_user_by_email(email)
            if not user:
                raise NotFoundException(resource="User", resource_id=email)
        
            if not self.hasher.verify(current_password, user.password):
                raise UnauthorizedException("Invalid password")

            changes: dict = {}
            if new_name is not None:
                changes["name"] = new_name
            if new_password is not None:
                changes["password"] = self.hasher.encrypt(new_password)
            if new_memo is not None:
                changes["memo"] = new_memo
            if new_role is not None:
                changes["role"] = new_role

            changes["updated_at"] = datetime.now(timezone.utc).replace(tzinfo=None)

            updated_user = await uow.user_repository.update(user.id, changes)
            return updated_user

    # ---------------------------------------------------------------------
    # Delete
    # ---------------------------------------------------------------------

    async def delete_user(self, user_id: str) -> bool:
        async with self.uow as uow:
            return await uow.user_repository.delete(user_id)
            


