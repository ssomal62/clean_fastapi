from pydantic import EmailStr
from fastapi import HTTPException, status
from app.common.security import create_access_token
from app.application.unit_of_work import UnitOfWork
from app.application.ports.password_hasher import PasswordHasher

class AuthService:
    
    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher):
        self.uow = uow
        self.hasher = hasher

    async def login(self, email: EmailStr, password: str) -> str:
        async with self.uow as uow:
            user = await uow.user_repository.find_by_email(email)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            if not self.hasher.verify(password, user.password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            access_token = create_access_token(
                    data={
                        "sub": user.id, 
                        "email": user.profile.email
                    },
                    role=user.role,
                )
            return access_token