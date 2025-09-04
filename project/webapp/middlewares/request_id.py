# ------------------------------------------------------------------------------
# 목적:
# - 각 HTTP 요청마다 고유한 Request ID를 생성/전파하고, 로그에도 자동으로 포함시킨다.
# - 클라이언트/게이트웨이가 미리 넣어준 X-Request-ID(또는 X-Correlation-ID)가 있으면 재사용한다.
# - 응답 헤더에 X-Request-ID를 항상 포함시켜 추적을 쉽게 한다.
# - 비동기 환경(uvicorn, FastAPI)에서 안전하게 요청별 값을 전달하기 위해 ContextVar 사용.
#
# 선택한 방식:
# - Starlette의 BaseHTTPMiddleware 대신 "순수 ASGI 미들웨어"를 사용.
#   이유) BaseHTTPMiddleware는 스트리밍/에러 전파 등 엣지 케이스에서 이슈가 보고됨.
#         ASGI를 직접 구현하면 오버헤드 적고 제어가 명확함.
# ------------------------------------------------------------------------------

import uuid
from contextvars import ContextVar
from typing import Iterable, Optional, Tuple

from starlette.types import ASGIApp, Receive, Scope, Send

# ------------------------------------------------------------------------------
# 요청별 컨텍스트 저장소:
# - 비동기 컨텍스트에서도 "요청 단위로" 안전하게 값을 보관하기 위해 ContextVar 사용
# ------------------------------------------------------------------------------
_request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """현재 요청 컨텍스트에 저장된 Request ID를 반환.
    - 미들웨어가 동작하지 않는 위치/타이밍에서는 None이 나올 수 있으니 주의."""
    return _request_id_var.get()


def set_request_id(value: str) -> None:
    """현재 요청 컨텍스트에 Request ID를 강제로 설정(권장 X)
    - 일반 사용자는 미들웨어가 자동으로 설정해주니 호출 필요 없음.
    - 테스트나 특수 상황에서만 사용."""
    _request_id_var.set(value)


class RequestIDASGIMiddleware:
    """Request ID를 주입/전파하는 ASGI 미들웨어.

    동작 요약:
    1) HTTP 요청 수신 시, 헤더에서 X-Request-ID 또는 X-Correlation-ID를 찾아 재사용.
       없으면 uuid4()로 신규 생성.
    2) ContextVar에 저장하여 같은 요청 컨텍스트에서 어디서든 get_request_id()로 사용 가능.
    3) 응답 시작 시점(http.response.start 메시지)에 X-Request-ID 헤더를 강제로 추가.
    4) scope['state']에도 request_id를 넣어 FastAPI Request.state.request_id로 접근 가능.
    """

    # 수용하는 inbound 헤더 이름(우선순위: 앞에서부터 검사)
    _inbound_header_candidates = (b"x-request-id", b"x-correlation-id")

    # 응답으로 무조건 내려보낼 표준 헤더 이름
    _outbound_header = b"x-request-id"

    def __init__(self, app: ASGIApp):
        self.app = app

    # ASGI 미들웨어 핵심: __call__(scope, receive, send)
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # HTTP 요청만 처리. (WebSocket 등은 그대로 패스)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # ------------------------------
        # 1) Request ID 추출/생성
        # ------------------------------
        headers: Iterable[Tuple[bytes, bytes]] = scope.get("headers", [])
        found: Optional[bytes] = None
        for key, value in headers:
            # 헤더 키는 모두 소문자 바이트로 들어옴. (ASGI 스펙)
            if key in self._inbound_header_candidates and value:
                found = value
                break

        if found:
            # 클라이언트/게이트웨이가 보낸 값을 그대로 재사용 (bytes → str)
            request_id = found.decode("latin1", errors="replace").strip()
        else:
            # 없으면 신규 생성
            request_id = str(uuid.uuid4())

        # ------------------------------
        # 2) ContextVar에 저장
        #    token은 try/finally로 reset하여 컨텍스트 누수 방지
        # ------------------------------
        token = _request_id_var.set(request_id)

        # ------------------------------
        # 3) scope.state에도 심어두면 FastAPI에서 request.state.request_id로 접근 가능
        #    (Starlette/FastAPI는 요청당 state 객체를 제공)
        # ------------------------------
        # state는 starlette에서 항상 제공하지만, 안전하게 기본 dict로 보장
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        # ------------------------------
        # 4) 응답 헤더에 X-Request-ID 강제 삽입을 위해 send를 래핑
        # ------------------------------
        async def send_wrapper(message):
            # 응답 시작 신호에서만 헤더를 주입
            if message["type"] == "http.response.start":
                # 기존 헤더 목록(list[tuple[bytes, bytes]])을 가져오고, 우리가 추가
                headers_list = list(message.get("headers", []))
                headers_list.append((self._outbound_header, request_id.encode("latin1")))
                # 필요하다면 X-Correlation-ID도 같이 넣고 싶다면 아래 주석 해제
                # headers_list.append((b"x-correlation-id", request_id.encode("latin1")))
                message["headers"] = headers_list
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # 요청이 끝나면 ContextVar 원복(메모리/컨텍스트 누수 방지)
            _request_id_var.reset(token)
