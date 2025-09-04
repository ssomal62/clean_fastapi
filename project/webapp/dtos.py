from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Literal

from pydantic import BaseModel, EmailStr, Field


# ============================================================================
# Auth DTOs
# ============================================================================

class LoginBody(BaseModel):
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=64)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================================
# User DTOs
# ============================================================================

RoleStr = Literal["ADMIN", "USER"]  # 도메인 Enum 대신 문자열 리터럴

class CreateUserBody(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    email: EmailStr = Field(max_length=64)
    password: str = Field(min_length=8, max_length=64)
    memo: str | None = None
    role: RoleStr = Field(default="USER")


class UpdateUserBody(BaseModel):
    email: EmailStr = Field(max_length=64)
    new_name: str | None = Field(min_length=1, max_length=32, default=None)
    current_password: str = Field(min_length=8, max_length=64)
    new_password: str | None = Field(min_length=8, max_length=64, default=None)
    new_memo: str | None = Field(default=None)
    new_role: RoleStr | None = Field(default=None)


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    memo: str | None
    updated_at: datetime


class UserPageResponse(BaseModel):
    users: list[UserResponse]
    next_cursor: Optional[str] = None


# ============================================================================
# Note DTOs
# ============================================================================

class CreateNoteBody(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1)
    memo_date: str = Field(min_length=8, max_length=8)
    tag_names: Optional[list[str]] | None = Field(default=None, min_length=1, max_length=32)


class UpdateNoteBody(BaseModel):
    title: str | None = Field(min_length=1, max_length=64, default=None)
    content: str | None = Field(min_length=1, default=None)
    memo_date: str | None = Field(min_length=8, max_length=8, default=None)
    tag_names: Optional[list[str]] | None = Field(default=None, min_length=1, max_length=32)


class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    memo_date: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime

class NotePageResponse(BaseModel):
    notes: list[NoteResponse]
    next_cursor: Optional[str] = None
    

# ============================================================================
# Error DTOs
# ============================================================================

class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    field: Optional[str] = Field(None, description="에러가 발생한 필드명")
    message: str = Field(..., description="에러 메시지")
    value: Optional[Any] = Field(None, description="에러가 발생한 값")


class ErrorResponse(BaseModel):
    """표준 에러 응답 스키마"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시간")
    status_code: int = Field(..., description="HTTP 상태 코드")
    error_code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: Optional[Dict[str, Any]] = Field(None, description="추가 상세 정보")
    errors: Optional[list[ErrorDetail]] = Field(None, description="필드별 에러 상세 정보")
    request_id: Optional[str] = Field(None, description="요청 ID")
    path: Optional[str] = Field(None, description="요청 경로")
    method: Optional[str] = Field(None, description="HTTP 메서드")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def model_dump(self, **kwargs):
        """JSON 직렬화 가능한 딕셔너리로 변환 (Pydantic v2)"""
        data = super().model_dump(**kwargs)
        # datetime을 ISO 문자열로 변환
        if 'timestamp' in data and isinstance(data['timestamp'], datetime):
            data['timestamp'] = data['timestamp'].isoformat()
        return data


class ValidationErrorResponse(ErrorResponse):
    """유효성 검증 에러 응답"""
    status_code: int = 400
    error_code: str = "VALIDATION_ERROR"
    message: str = "Validation failed"
    errors: list[ErrorDetail] = Field(..., description="유효성 검증 실패 상세 정보")


class NotFoundErrorResponse(ErrorResponse):
    """리소스 없음 에러 응답"""
    status_code: int = 404
    error_code: str = "NOT_FOUND"
    message: str = "Resource not found"


class UnauthorizedErrorResponse(ErrorResponse):
    """인증 실패 에러 응답"""
    status_code: int = 401
    error_code: str = "UNAUTHORIZED"
    message: str = "Unauthorized"


class ForbiddenErrorResponse(ErrorResponse):
    """권한 부족 에러 응답"""
    status_code: int = 403
    error_code: str = "FORBIDDEN"
    message: str = "Forbidden"


class ConflictErrorResponse(ErrorResponse):
    """리소스 충돌 에러 응답"""
    status_code: int = 409
    error_code: str = "CONFLICT"
    message: str = "Resource conflict"


class InternalServerErrorResponse(ErrorResponse):
    """내부 서버 에러 응답"""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "Internal server error"
