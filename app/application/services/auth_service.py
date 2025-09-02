from pydantic import EmailStr
from fastapi import HTTPException, status
from app.domain.user_repository import UserRepository
from app.common.security import create_access_token
from app.application.unit_of_work import UnitOfWork
from utils.crypto import Crypto

class AuthService:
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.crypto = Crypto()

    async def login(self, email: EmailStr, password: str) -> str:
        async with self.uow as uow:
            user = await uow.user_repository.find_by_email(email)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            if not self.crypto.verify(password, user.password):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            access_token = create_access_token(
                    data={
                        "sub": user.id, 
                        "email": user.profile.email
                    },
                    role=user.role,
                )
            return access_token