from fastapi import status
from pydantic import EmailStr

from ..infrastructure.argon2_password_hasher import Argon2PasswordHasher as PasswordHasher
from ..infrastructure.unit_of_work import SqlAlchemyUnitOfWork as UnitOfWork
from ..infrastructure.jwt_provider import JwtProvider
from ..shared.exceptions import NotFoundException, UnauthorizedException


class AuthService:
    
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, jwt_provider: JwtProvider):
        self.uow = uow
        self.hasher = hasher
        self.jwt_provider = jwt_provider

    async def login(self, email: EmailStr, password: str) -> str:
        async with self.uow as uow:
            user = await uow.user_repository.find_by_email(email)

            if not user:
                raise NotFoundException(resource="User", resource_id=email)

            if not self.hasher.verify(password, user.password):
                raise UnauthorizedException("Invalid credentials")

            access_token = self.jwt_provider.create_access_token(
                    data={
                        "sub": user.id, 
                        "email": user.profile.email
                    },
                    role=user.role,
                )
            return access_token