# ------------------------------------------------------------------------------
# 목적:
# - 모든 요청/응답/에러를 구조화(JSON)하여 표준 출력으로 기록
# - Request ID를 헤더에서 재사용하거나(uuid4) 생성하여 ContextVar로 전파
# - 4xx/5xx 레벨에 맞춰 실제 logging 레벨 사용 (info/warning/error)
# - 응답 크기는 Response.body가 있을 때만 기록(Streaming 대응은 별도 Perf 미들웨어 권장)
#
# 참고:
# - Request ID는 다른 미들웨어/핸들러에서도 get_request_id()로 조회 가능
# - 이미 별도의 RequestID 미들웨어가 있다면 중복 생성을 피하도록 여기서 "재사용 우선"
# ------------------------------------------------------------------------------

import asyncio
import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ------------------------------------------------------------------------------
# 요청 스코프 Request ID 저장용 ContextVar
# - 비동기(코루틴) 환경에서 요청 단위 격리 보장
# ------------------------------------------------------------------------------
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """현재 요청 컨텍스트의 Request ID 반환(없을 수도 있음)."""
    return request_id_var.get()


class StructuredLogger:
    """구조화(JSON) 로깅 헬퍼.

    - 표준 출력(StreamHandler)로 JSON 문자열을 남깁니다.
    - 실제 로그 레벨(logging.INFO/ WARNING/ ERROR)을 함께 사용합니다.
    - 추가 필드는 dict로 확장 가능(ELK/Vector/Fluent 등 수집기에서 파싱 용이).
    """

    def __init__(self, name: str = "fastapi"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)  # 상한선(필요 시 설정에서 조정)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            # 메시지는 JSON 문자열 그대로 쏩니다.
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    # ---- 공용: 공통 필드 만들기 ------------------------------------------------
    @staticmethod
    def _base(level: str, log_type: str, request_id: Optional[str]) -> dict:
        # UTC ISO8601(Z) 타임스탬프
        return {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level,
            "type": log_type,
            "request_id": request_id or "-",  # 빈 값 방지
        }

    # ---- 요청 ------------------------------------------------------------------
    def log_request(
        self,
        *,
        request_id: Optional[str],
        method: str,
        url: str,
        client_ip: str,
        user_agent: str,
        content_length: Optional[int],
    ):
        payload = self._base("INFO", "request", request_id)
        payload.update(
            {
                "method": method,
                "url": url,
                "client_ip": client_ip,
                "user_agent": user_agent,
                "content_length": content_length,
            }
        )
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    # ---- 응답 ------------------------------------------------------------------
    def log_response(
        self,
        *,
        request_id: Optional[str],
        status_code: int,
        response_time_ms: float,
        response_size: Optional[int],
    ):
        # 상태코드에 따라 실제 로그 레벨 결정
        if status_code >= 500:
            level = "ERROR"
            emit = self.logger.error
        elif status_code >= 400:
            level = "WARN"
            emit = self.logger.warning
        else:
            level = "INFO"
            emit = self.logger.info

        payload = self._base(level, "response", request_id)
        payload.update(
            {
                "status_code": status_code,
                "response_time_ms": round(response_time_ms, 2),
                "response_size": response_size,  # Streaming은 None일 수 있음
            }
        )
        emit(json.dumps(payload, ensure_ascii=False))

    # ---- 에러 -------------------------------------------------------------------
    def log_error(
        self,
        *,
        request_id: Optional[str],
        error: Exception,
        method: str,
        url: str,
        client_ip: str,
    ):
        payload = self._base("ERROR", "error", request_id)
        payload.update(
            {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "method": method,
                "url": url,
                "client_ip": client_ip,
            }
        )
        # stack 정보는 logging이 붙여줌
        self.logger.error(json.dumps(payload, ensure_ascii=False), exc_info=True)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    구조화 로깅 미들웨어
    ----------------------------------------------------------------------
    동작:
      1) Request ID 결정:
         - 클라이언트/프록시가 보낸 X-Request-ID / X-Correlation-ID가 있으면 "재사용"
         - 없으면 uuid4() 생성
         - ContextVar에 set → 동일 요청 컨텍스트에서 get_request_id()로 접근
      2) 요청 로그 기록
      3) 실제 핸들러 호출 후 응답 로그 기록(처리시간/응답크기)
      4) 예외 발생 시 에러 로그 기록
      5) 항상 응답 헤더에 X-Request-ID 추가
    주의:
      - StreamingResponse는 response.body가 없을 수 있어 응답 크기 추정 불가(None)
        → 전체 전송 바이트가 필요하면 PerformanceMiddleware에서 send 래핑으로 측정 권장
    """

    def __init__(self, app: ASGIApp, logger_name: str = "fastapi"):
        super().__init__(app)
        self.logger = StructuredLogger(logger_name)

    async def dispatch(self, request: Request, call_next):
        # 1) Request ID 결정: 헤더 우선 재사용 → 없으면 신규 생성
        header_req_id = (
            request.headers.get("x-request-id")
            or request.headers.get("x-correlation-id")
        )
        request_id = header_req_id.strip() if header_req_id else str(uuid.uuid4())

        # ContextVar에 저장(토큰으로 나중에 reset)
        token = request_id_var.set(request_id)

        # 고해상도 타이머
        start = time.perf_counter()

        # 클라이언트 메타
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "") or "-"
        content_length = self._safe_int(request.headers.get("content-length"))

        # 2) 요청 로그
        self.logger.log_request(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=user_agent,
            content_length=content_length,
        )

        try:
            # 3) 실제 처리
            response = await call_next(request)

            # 처리 시간(ms)
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            # 응답 크기: .body가 있을 때만(Streaming은 None)
            response_size = None
            if hasattr(response, "body") and isinstance(response.body, (bytes, bytearray)):
                response_size = len(response.body)

            # 응답 헤더에 Request ID 추가(최종 응답에 노출)
            response.headers.setdefault("X-Request-ID", request_id)

            # 응답 로그
            self.logger.log_response(
                request_id=request_id,
                status_code=response.status_code,
                response_time_ms=elapsed_ms,
                response_size=response_size,
            )

            return response

        except Exception as e:
            # 4) 예외 로그 (스택 포함)
            self.logger.log_error(
                request_id=request_id,
                error=e,
                method=request.method,
                url=str(request.url),
                client_ip=client_ip,
            )
            raise

        finally:
            # 5) ContextVar 원복(누수 방지)
            request_id_var.reset(token)

    # ----------------------------------------------------------------------
    # 유틸
    # ----------------------------------------------------------------------
    @staticmethod
    def _safe_int(value: Optional[str]) -> Optional[int]:
        """정수 파싱(실패 시 None)."""
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """프록시/로드밸런서 환경 고려한 클라이언트 IP 추출."""
        # X-Forwarded-For: "client, proxy1, proxy2"
        xff = request.headers.get("x-forwarded-for")
        if xff:
            first = xff.split(",")[0].strip()
            if first:
                return first

        # X-Real-IP
        xrip = request.headers.get("x-real-ip")
        if xrip:
            return xrip

        # 직접 연결 소켓
        return request.client.host if request.client else "unknown"


# 전역 로거 인스턴스(원한다면 DI/싱글턴 컨테이너로 관리)
structured_logger = StructuredLogger()
