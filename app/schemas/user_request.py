from pydantic import BaseModel, EmailStr, Field
from app.domain.user import Role

class CreateUserBody(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=64)
    memo: str | None = None
    role: Role  = Field(default=Role.USER)

class UpdateUserBody(BaseModel):
    email: EmailStr = Field(max_length=64)
    new_name: str | None = Field(min_length=1, max_length=32, default=None)
    current_password: str = Field(min_length=8, max_length=64)
    new_password: str | None = Field(min_length=8, max_length=64, default=None)
    new_memo: str | None = Field(default=None)
    new_role: Role | None = Field(default=None)