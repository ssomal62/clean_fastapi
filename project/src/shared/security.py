# ------------------------------------------------------------------------------
# 목적:
# - 공통 보안 헤더 자동 주입으로 기본 보안 수준 상향
# - 환경(dev/prod)에 따른 CSP 차등 적용
# - 옵션: WebSocket 허용, CSP nonce, Report-Only, 제외 경로, HSTS preload 제어
#
# 참고:
# - BaseHTTPMiddleware 사용: 헤더 주입만 하므로 간단/안전
# - 더 미세 제어가 필요하면 ASGI 미들웨어로 전환 가능
# ------------------------------------------------------------------------------

import os
import secrets
from typing import Iterable, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 미들웨어
    ------------------------------------------------------
    1) 공통 헤더: X-Content-Type-Options, Referrer-Policy, COOP, Permissions-Policy,
                 Origin-Agent-Cluster, Cross-Origin-Resource-Policy, X-DNS-Prefetch-Control
    2) CSP:
       - prod: 보수적 정책, inline/eval 불허(옵션: nonce)
       - dev: 디버깅 편의 허용(unsafe-inline/unsafe-eval)
       - 옵션: Report-Only, 추가 connect-src 호스트, WebSocket 허용
    3) HSTS: prod + HTTPS에서만. (옵션: preload 플래그)
    4) 제외 경로: /health, /metrics, /docs 등은 필요 시 제외
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        env: str | None = None,
        allow_ws: bool = False,
        exclude_paths: tuple[str, ...] = ("/health", "/metrics"),
        csp_report_only: bool = False,
        csp_additional_connect_hosts: tuple[str, ...] = (),  # 예: ("https://api.example.com",)
        enable_nonce: bool = False,  # 템플릿/프론트에서 nonce 사용 시 True
        hsts_preload: bool = False,  # 도메인이 preload 등록된 경우에만 True 권장
    ):
        super().__init__(app)
        # env 정규화: prod/production → "prod", 나머지 → "dev"
        raw_env = env or os.getenv("APP_ENV", "dev")
        self.env = "prod" if raw_env.lower() in ("prod", "production") else "dev"

        self.allow_ws = allow_ws
        self.exclude_paths = exclude_paths
        self.csp_report_only = csp_report_only
        self.csp_additional_connect_hosts = csp_additional_connect_hosts
        self.enable_nonce = enable_nonce
        self.hsts_preload = hsts_preload

    async def dispatch(self, request: Request, call_next):
        # 제외 경로는 통과 (문서/헬스체크 등에서 CSP로 인한 노이즈 최소화)
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        # 요청별 CSP nonce 생성(옵션)
        # - 템플릿에서 <script nonce="{{ request.state.csp_nonce }}"> 형태로 사용
        nonce = None
        if self.enable_nonce:
            nonce = secrets.token_urlsafe(16)
            # 다른 레이어(템플릿/응답 생성)에서 쓰도록 state에 노출
            request.state.csp_nonce = nonce  # type: ignore[attr-defined]

        response = await call_next(request)

        # ---------------------------
        # 1) 공통 보안 헤더 (환경 무관)
        # ---------------------------
        # MIME 스니핑 방지
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # Referrer 최소화
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Cross-Origin-Opener-Policy(탭 간 격리)
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # 권한 제한(필요 권한만 허용)
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), fullscreen=(self)"
        )
        # 사이트 격리(신규 크롬/파폭): 힙 격리로 사이드채널 완화
        response.headers.setdefault("Origin-Agent-Cluster", "?1")
        # 리소스 접근 범위 제한(동/타 사이트에서 리소스 차단 정책)
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        # DNS prefetch 비활성화(원치 않는 프리페치 방지)
        response.headers.setdefault("X-DNS-Prefetch-Control", "off")

        # X-Frame-Options는 frame-ancestors로 대체 가능(레거시 호환이 필요하면 켜세요)
        # response.headers.setdefault("X-Frame-Options", "DENY")

        # ---------------------------
        # 2) 환경별 CSP
        # ---------------------------
        if self.env == "prod":
            connect_src_parts: list[str] = ["'self'", "https:"]
            if self.allow_ws:
                connect_src_parts += ["wss:"]
            if self.csp_additional_connect_hosts:
                connect_src_parts += list(self.csp_additional_connect_hosts)

            # prod: inline/eval 지양. nonce 사용 시 script-src에 nonce 부여
            script_src = ["'self'"]
            if nonce:
                # nonce 사용 시 strict-dynamic를 함께 쓰면 동적으로 로드되는 스크립트까지 보호 가능(선택)
                # script_src += [f"'nonce-{nonce}'", "'strict-dynamic'"]
                script_src += [f"'nonce-{nonce}'"]
            # 스타일은 현실적으로 inline 허용하는 경우가 많음(필요에 따라 제거)
            style_src = ["'self'", "'unsafe-inline'"]

            csp = (
                "default-src 'self'; "
                f"script-src {' '.join(script_src)}; "
                f"style-src {' '.join(style_src)}; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                f"connect-src {' '.join(connect_src_parts)}; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

            # Report-Only 지원(스테이징에서 점검할 때 유용)
            csp_header_name = "Content-Security-Policy-Report-Only" if self.csp_report_only else "Content-Security-Policy"
            response.headers.setdefault(csp_header_name, csp)

            # HSTS: HTTPS에서만 적용 (로컬/프록시 환경 주의)
            if request.url.scheme == "https":
                # preload 플래그는 크롬 preload 리스트 등록 도메인에만 권장
                hsts_value = "max-age=31536000; includeSubDomains"
                if self.hsts_preload:
                    hsts_value += "; preload"
                response.headers.setdefault("Strict-Transport-Security", hsts_value)

        else:
            # dev: 개발 편의성 우선(unsafe-inline/unsafe-eval 허용)
            connect_src_parts: list[str] = ["'self'", "http:", "https:"]
            if self.allow_ws:
                connect_src_parts += ["ws:", "wss:"]
            if self.csp_additional_connect_hosts:
                connect_src_parts += list(self.csp_additional_connect_hosts)

            dev_csp = (
                "default-src 'self' http: https: data: blob:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' http: https:; "
                "style-src 'self' 'unsafe-inline' http: https:; "
                "img-src 'self' data: http: https:; "
                "font-src 'self' http: https:; "
                f"connect-src {' '.join(connect_src_parts)}; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
            # dev에서도 다른 레이어가 CSP를 이미 넣었다면 덮지 않도록 setdefault 사용
            response.headers.setdefault("Content-Security-Policy", dev_csp)

        return response
