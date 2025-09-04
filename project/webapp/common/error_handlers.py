# ------------------------------------------------------------------------------
# 목적:
# - FastAPI 전체 예외를 표준 ErrorResponse 스키마로 일관되게 반환
# - Pydantic ValidationError, HTTPException, 커스텀 예외, DB 예외, 기타 모든 예외 처리
# - 환경별(stack trace 노출 통제), Request ID 포함, 경로/메서드 포함
# ------------------------------------------------------------------------------

import traceback
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ...src.shared.exceptions import BaseAppException
from ..middlewares.request_id import get_request_id
from ..settings import WebAppSettings
from ..dtos import (ConflictErrorResponse, ErrorDetail,
                                        ErrorResponse, ForbiddenErrorResponse,
                                        InternalServerErrorResponse,
                                        NotFoundErrorResponse,
                                        UnauthorizedErrorResponse,
                                        ValidationErrorResponse)


settings = WebAppSettings()

# --------------------------------------------------------------------------
# 유틸: Pydantic v1/v2 호환 응답 시리얼라이즈
# --------------------------------------------------------------------------
def _to_dict(model) -> Dict[str, Any]:
    """Pydantic v1(.dict) / v2(.model_dump) 호환 헬퍼."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    elif hasattr(model, "dict"):
        return model.dict()
    else:
        return model

# --------------------------------------------------------------------------
# 표준 에러 응답 생성기
# --------------------------------------------------------------------------
def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request: Request,
    details: Optional[Dict[str, Any]] = None,
    errors: Optional[List[ErrorDetail]] = None,
) -> ErrorResponse:
    """표준 에러 응답 생성 (Request ID/경로/메서드 포함)."""
    return ErrorResponse(
        status_code=status_code,
        error_code=error_code,
        message=message,
        details=details,
        errors=errors,
        request_id=get_request_id(),
        path=str(request.url.path),
        method=request.method,
    )

# --------------------------------------------------------------------------
# Validation 에러
# --------------------------------------------------------------------------
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Pydantic 유효성 검증 에러 핸들러.
    - loc은 ("body", "field", 0, ...) 등 다양한 타입이 섞일 수 있어 str 변환 안전 처리
    - input 값은 v2에서 없을 수 있으므로 get 사용
    """
    error_items: List[ErrorDetail] = []
    for e in exc.errors():
        # loc 안전 조인
        loc = e.get("loc", [])
        field = ".".join(str(x) for x in loc) if loc else ""
        error_items.append(
            ErrorDetail(
                field=field,
                message=e.get("msg", "Invalid input"),
                value=e.get("input"),
            )
        )

    res = ValidationErrorResponse(
        errors=error_items,
        request_id=get_request_id(),
        path=str(request.url.path),
        method=request.method,
    )
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=_to_dict(res))

# --------------------------------------------------------------------------
# 커스텀 애플리케이션 예외
# --------------------------------------------------------------------------
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """
    BaseAppException: 서비스 레이어에서 명시적으로 던지는 예외.
    - 상태코드/에러코드/메시지/디테일을 그대로 사용.
    """
    res = create_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.message,
        request=request,
        details=exc.details,
    )
    return JSONResponse(status_code=exc.status_code, content=_to_dict(res))

# --------------------------------------------------------------------------
# HTTPException (FastAPI 기본)
# --------------------------------------------------------------------------
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    FastAPI HTTPException → 타입별 스키마로 매핑.
    - 401/403/404/409 등은 전용 응답 모델로 내려주면 관측성이 좋아짐.
    - detail은 str/Dict 등 다양한 타입이 올 수 있어 str로 방어적 캐스팅.
    """
    code = exc.status_code
    msg = str(exc.detail) if exc.detail is not None else "HTTP error"

    if code == status.HTTP_401_UNAUTHORIZED:
        res = UnauthorizedErrorResponse(
            message=msg,
            request_id=get_request_id(),
            path=str(request.url.path),
            method=request.method,
        )
    elif code == status.HTTP_403_FORBIDDEN:
        res = ForbiddenErrorResponse(
            message=msg,
            request_id=get_request_id(),
            path=str(request.url.path),
            method=request.method,
        )
    elif code == status.HTTP_404_NOT_FOUND:
        res = NotFoundErrorResponse(
            message=msg,
            request_id=get_request_id(),
            path=str(request.url.path),
            method=request.method,
        )
    elif code == status.HTTP_409_CONFLICT:
        res = ConflictErrorResponse(
            message=msg,
            request_id=get_request_id(),
            path=str(request.url.path),
            method=request.method,
        )
    else:
        # 그 외는 일반 포맷으로
        res = create_error_response(
            status_code=code,
            error_code="HTTP_ERROR",
            message=msg,
            request=request,
        )

    return JSONResponse(status_code=code, content=_to_dict(res))

# --------------------------------------------------------------------------
# DB 예외
# --------------------------------------------------------------------------
async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    SQLAlchemyError: 클라이언트에 과도한 정보 노출 금지.
    - 메시지는 일반화, 타입 정도만 details로 실어주고 상세는 서버 로그로.
    """
    res = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="DATABASE_ERROR",
        message="Database operation failed",
        request=request,
        details={"error_type": type(exc).__name__},
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=_to_dict(res))

# --------------------------------------------------------------------------
# 일반 예외 (최후 보루)
# --------------------------------------------------------------------------
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    일반 예외: 운영 환경에선 스택트레이스 미노출, 개발에서만 제한적으로 노출.
    - settings.debug 또는 app.state.debug를 참조해 조건부 포함.
    - 응답 폭주 방지를 위해 trace 길이 제한 권장.
    """
    show_trace = bool(getattr(settings, "debug", False) or getattr(request.app.state, "debug", False))

    details: Dict[str, Any] = {}
    if show_trace:
        tb = traceback.format_exc()
        # 너무 긴 스택 방지(예: 8KB 제한)
        details["traceback"] = tb[:8192]

    res = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        request=request,
        details=details or None,
    )
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=_to_dict(res))

# --------------------------------------------------------------------------
# 등록 함수
# --------------------------------------------------------------------------
def register_exception_handlers(app) -> None:
    """
    FastAPI 앱에 예외 핸들러 등록.
    - 등록 순서 중요 X (타입 매칭으로 분기)
    - 서버 로그엔 미들웨어(로깅)에서 에러 기록이 남는 구조가 바람직.
    """
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException,            http_exception_handler)
    app.add_exception_handler(BaseAppException,         app_exception_handler)
    app.add_exception_handler(SQLAlchemyError,          database_exception_handler)
    app.add_exception_handler(Exception,                general_exception_handler)
