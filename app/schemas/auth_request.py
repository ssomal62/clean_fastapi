from pydantic import BaseModel, EmailStr, Field

class LoginBody(BaseModel):
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=64)