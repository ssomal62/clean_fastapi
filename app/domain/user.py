from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

# 값객체(value object) => id속성없이 도메인 데이터만 가지고 있는 객채
@dataclass
class Profile:
    name: str
    email: str

@dataclass
class User:
    id: str
    profile: Profile
    password: str
    memo: str | None
    role: Role
    created_at:datetime
    updated_at:datetime
