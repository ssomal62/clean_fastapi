# setup_middleware.py
# ------------------------------------------------------------------------------
# 목적:
# - FastAPI 애플리케이션에 필요한 미들웨어들을 중앙집중적으로 설정
# - 미들웨어 순서는 매우 중요 → 바깥쪽(먼저 실행)에서 안쪽(나중 실행)으로 감싸짐
# - 여기서는 로깅 → 성능 모니터링 → CORS → 보안 헤더 순으로 배치
# ------------------------------------------------------------------------------

from fastapi import FastAPI
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from ..middlewares.logging import LoggingMiddleware
from ..middlewares.performance import PerformanceMiddleware
from ..middlewares.request_id import RequestIDASGIMiddleware


def setup_middleware(app: FastAPI):
    """
    모든 전역 미들웨어를 등록한다.
    순서:
      1) 로깅
      2) 성능 모니터링
      3) CORS
      4) 보안 헤더
      (옵션) HTTPS 리다이렉트, TrustedHost
    """

    # ------------------------------------------------------------------
    # --- (선택) 프로덕션 환경 보안 강제 미들웨어
    # ------------------------------------------------------------------
    # HTTPSRedirectMiddleware:
    #   - HTTP 요청을 자동으로 HTTPS로 301 리다이렉트
    #   - 로컬/개발 환경에서는 불편할 수 있으므로 prod에서만 활성화
    #
    # TrustedHostMiddleware:
    #   - Host 헤더 위조 공격 방지
    #   - allowed_hosts에 지정된 도메인/서브도메인만 허용
    #   - 예: ["example.com", "*.example.com"]
    #
    # if settings.environment == "prod" and settings.enable_https_redirect:
    #     app.add_middleware(HTTPSRedirectMiddleware)
    #
    # if settings.environment == "prod" and settings.trusted_hosts:
    #     app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    # ------------------------------------------------------------------
    # 1) Request ID (가장 바깥쪽)
    # ------------------------------------------------------------------
    # - 각 요청마다 고유한 Request ID 생성/전파
    # - 다른 미들웨어에서 get_request_id()로 접근 가능
    # - 응답 헤더에 X-Request-ID 자동 추가
    app.add_middleware(RequestIDASGIMiddleware)

    # ------------------------------------------------------------------
    # 2) 로깅
    # ------------------------------------------------------------------
    # - 모든 요청/응답을 관찰
    # - request_id, trace_id 같은 context를 포함해 구조화 로그 출력
    # - Request ID 미들웨어 다음에 실행되어 Request ID를 로그에 포함
    app.add_middleware(LoggingMiddleware)

    # ------------------------------------------------------------------
    # 2) 성능 모니터링
    # ------------------------------------------------------------------
    # - 요청 처리 시간을 ms 단위로 측정
    # - 응답 크기(bytes), 상태코드, slow request 여부를 로그로 남김
    # - 브라우저 Network 탭에서 확인 가능한 Server-Timing 헤더도 추가
    # - /health, /metrics 같은 경로는 자동으로 제외
    # if settings.enable_performance_monitoring:
    #     app.add_middleware(PerformanceMiddleware)

    # ------------------------------------------------------------------
    # 3) CORS (Cross-Origin Resource Sharing)
    # ------------------------------------------------------------------
    # - 브라우저의 cross-origin 요청 허용/차단 제어
    # - preflight(OPTIONS) 요청을 빠르게 처리해야 클라이언트 지연이 줄어듦
    # - dev 환경에서 프론트엔드(localhost:3000 등)와 연동할 때 주로 사용
    #
    # if settings.enable_cors:
    #     # 예시: setup_cors(app) 함수에서 CORSMiddleware 등록
    #     # from fastapi.middleware.cors import CORSMiddleware
    #     # app.add_middleware(CORSMiddleware, allow_origins=[...], ...)
    #     setup_cors(app)

    # ------------------------------------------------------------------
    # 4) 보안 헤더 (응답 직전 헤더 덮어쓰기)
    # ------------------------------------------------------------------
    # - 모든 응답에 X-Content-Type-Options, Referrer-Policy, CSP, HSTS 등
    #   보안 권장 헤더를 자동 주입
    # - prod/dev에 따라 CSP를 엄격/완화 버전으로 분기
    # - 미들웨어 체인의 마지막에 두는 것이 안전:
    #   → 다른 미들웨어/라우터에서 헤더를 추가하더라도 최종적으로
    #      보안 헤더가 보장됨
    # if settings.enable_security_headers:
    #     app.add_middleware(SecurityHeadersMiddleware)
