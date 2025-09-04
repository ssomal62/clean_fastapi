# ------------------------------------------------------------------------------
# 목적:
# - 각 HTTP 요청에 대한 성능 지표를 수집/로그로 기록
# - 처리 시간(ms), 응답 크기(bytes), 상태코드, 느린 요청 감지
# - Server-Timing 헤더를 응답에 추가하여 브라우저 개발자도구(Network 탭)에서 확인 가능
# - StreamingResponse(청크 단위 전송)까지 대응
# - 실무에서 불필요한 요청(/health, /metrics, OPTIONS 등)을 모니터링에서 자동 제외
#
# 구현 방식:
# - "ASGI 미들웨어" 방식으로 작성 (BaseHTTPMiddleware 미사용)
#   → 고성능 + edge case 대응
# ------------------------------------------------------------------------------

import time

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Receive, Scope, Send

from ..middlewares.logging import structured_logger as log


class PerformanceMiddleware:
    """
    ASGI 기반 성능 모니터링 미들웨어
    ------------------------------------------------
    1) 요청 시작 시점 기록
    2) 응답 이벤트를 가로채서:
       - 상태코드 확인
       - Server-Timing 헤더 추가
       - body 크기(bytes) 누적
    3) 요청 종료 후 전체 처리 시간 계산
    4) slow_ms 임계값을 초과하면 WARN, 아니면 INFO 레벨로 로그 기록
    5) 예외 발생 시에도 처리 시간 기록 후 exception 로그 남김
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_ms: int = 1000,                       # 느린 요청(slow request) 판별 기준(ms 단위)
        exclude_paths: tuple[str, ...] = ("/health", "/metrics"),  # 모니터링 제외할 경로 prefix
        sample_options: bool = False,              # OPTIONS 요청(CORS preflight)도 기록할지 여부
    ) -> None:
        self.app = app
        self.slow_ms = slow_ms
        self.exclude_paths = exclude_paths
        self.sample_options = sample_options

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        ASGI 엔트리포인트
        ------------------------------------------------
        scope : 요청 관련 메타데이터 (method, path, headers 등)
        receive : 클라이언트 → 서버 이벤트 스트림
        send : 서버 → 클라이언트 이벤트 스트림
        """
        if scope["type"] != "http":
            # HTTP 요청만 처리, 나머지(websocket, lifespan 등)는 그대로 통과
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "-")
        path = scope.get("path", "-")

        # ------------------------------------------------
        # 모니터링 제외 규칙 적용
        # ------------------------------------------------
        if (
            (not self.sample_options and method == "OPTIONS")   # OPTIONS 무시 (CORS preflight)
            or any(path.startswith(p) for p in self.exclude_paths)  # /health, /metrics 등 무시
        ):
            await self.app(scope, receive, send)
            return

        # ------------------------------------------------
        # 요청 시작 시각 기록 (perf_counter → 고정밀 타이머)
        # ------------------------------------------------
        start = time.perf_counter()
        bytes_sent = 0     # 응답 body 크기(누적)
        status_code = 0    # 상태코드 추적 (초기값은 0)

        async def send_wrapper(event):
            """
            send() 래퍼:
              - http.response.start 이벤트에서 상태코드와 헤더를 가로챔
              - http.response.body 이벤트에서 body 크기를 합산
            """
            nonlocal bytes_sent, status_code

            if event["type"] == "http.response.start":
                # 응답 시작 이벤트
                status_code = event.get("status", 0)

                # 헤더 수정 (Server-Timing 추가)
                headers = MutableHeaders(raw=event.setdefault("headers", []))
                dur_ms = int((time.perf_counter() - start) * 1000)
                headers.append("Server-Timing", f"app;desc=fastapi;dur={dur_ms}")

            elif event["type"] == "http.response.body":
                # body 이벤트 (스트리밍 시 여러번 호출될 수 있음)
                body = event.get("body", b"") or b""
                bytes_sent += len(body)

            # 원래 send 호출
            await send(event)

        # ------------------------------------------------
        # 요청 처리 try/finally → 예외가 발생해도 성능 로그는 남김
        # ------------------------------------------------
        try:
            # 실제 앱 호출 (ASGI 파이프라인 이어가기)
            await self.app(scope, receive, send_wrapper)

            # 요청 처리 시간 계산
            total_ms = (time.perf_counter() - start) * 1000.0

            # 로그 레벨 결정 (느린 요청이면 warning, 아니면 info)
            level = "warning" if total_ms > self.slow_ms else "info"

            getattr(log.logger, level)(
                "perf",
                extra={
                    "type": "performance",
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "total_time_ms": round(total_ms, 2),
                    "response_size_bytes": bytes_sent,
                    "is_slow": total_ms > self.slow_ms,
                },
            )

        except Exception:
            # 예외가 발생했을 때도 성능 데이터 남김
            total_ms = (time.perf_counter() - start) * 1000.0

            log.logger.exception(
                "perf_error",
                extra={
                    "type": "performance",
                    "method": method,
                    "path": path,
                    "status_code": status_code or 500,  # 실패 시 기본 500
                    "total_time_ms": round(total_ms, 2),
                },
            )
            # 예외 재전파 → FastAPI가 에러 응답 처리
            raise
