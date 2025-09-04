# ------------------------------------------------------------------------------
# 목적:
# - Kubernetes/로드밸런서/모니터링에서 사용할 헬스 엔드포인트 제공
# - /health           : 가벼운 가용성 체크(캐시 방지 헤더 포함)
# - /health/detailed  : DB/시스템 지표 포함(운영 노출은 플래그로 제어 권장)
# - /health/ready     : 의존성(예: Postgres, RabbitMQ) 연결 가능 여부
# - /health/live      : 프로세스 생존 여부(의존성 체크 X)
#
# 설계 포인트:
# - 캐시 방지: Cache-Control/Pragma 헤더 강제
# - 빠른 실패: DB/RabbitMQ 체크는 짧은 타임아웃
# - 보수적 공개: detailed는 내부/인증 경로 또는 플래그로만 노출
# ------------------------------------------------------------------------------

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional, Tuple

import psutil
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...src.infrastructure.settings import infrastructure_settings
from ..settings import settings


# (선택) RabbitMQ 체크용. 미설치 환경도 고려하여 optional import 처리.
try:
    import aio_pika  # pip install aio-pika
except Exception:  # ImportError 포함
    aio_pika = None  # type: ignore

router = APIRouter(prefix="/health", tags=["health"])


# ------------------------------------------------------------------------------
# 공통 유틸
# ------------------------------------------------------------------------------
def _now_iso() -> str:
    """UTC ISO8601(Z) 타임스탬프 반환 (로그/모니터링 표준 포맷)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _no_store_headers(resp: Response) -> None:
    """캐시 방지 헤더 강제 (프록시/브라우저 캐시 회피)."""
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"


async def _db_ping(db: AsyncSession, timeout_s: float = 1.0) -> Tuple[bool, Optional[str]]:
    """PostgreSQL ping: 간단한 SELECT 1. 타임아웃/예외 처리."""
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=timeout_s)
        return True, None
    except Exception as e:
        return False, str(e)


async def _rabbitmq_ping(url: str, timeout_s: float = 1.0) -> Tuple[bool, Optional[str]]:
    """
    RabbitMQ ping: aio-pika로 커넥션/채널 오픈 후 즉시 종료.
    - 미설치/비활성 환경에서도 graceful 하게 동작.
    - url 예: amqp://user:pass@host:5672/ 또는 amqps://...
    """
    if aio_pika is None:
        return False, "aio-pika not installed"

    try:
        conn = await asyncio.wait_for(aio_pika.connect_robust(url), timeout=timeout_s)
        try:
            ch = await asyncio.wait_for(conn.channel(), timeout=timeout_s)
            await ch.close()
        finally:
            await conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------------------------
# DB 세션 의존성
# ------------------------------------------------------------------------------
async def get_db_session():
    """
    NOTE: 현재 예시는 매 요청마다 컨테이너를 새로 만드는 형태라 오버헤드가 있을 수 있음.
    - 실제 운영에선 DI 컨테이너에서 session_factory를 앱 시작 시 주입 받아 재사용 권장.
    - 예: app.dependency_overrides 또는 FastAPI startup 이벤트에서 주입.
    """
    from ..container import MainContainer
    container = MainContainer()
    session_factory = container.infrastructure.session_factory()
    async with session_factory() as session:
        yield session


# ------------------------------------------------------------------------------
# 라우트
# ------------------------------------------------------------------------------
@router.get("/")
async def health_check(response: Response):
    """
    L4/L7에서 빠르게 확인하는 기본 헬스 체크.
    - 의존성 체크 X, 가벼운 JSON만 반환.
    - 캐시 방지 헤더 포함.
    """
    _no_store_headers(response)
    return {
        "status": "healthy",
        "timestamp": _now_iso(),
        "service": "clean-fastapi",
        "version": settings.APP_VERSION,
    }


@router.get("/detailed")
async def detailed_health_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    상세 헬스 체크 (DB + 시스템 지표).
    ⚠️ 운영에선 settings.enable_detailed_health 같은 플래그로 노출 제어 권장.
    """
    _no_store_headers(response)

    # DB 연결 상태
    db_ok, db_err = await _db_ping(db, timeout_s=1.0)
    db_status = "healthy" if db_ok else f"unhealthy: {db_err}"

    # 시스템 지표 (컨테이너/권한 제한 환경에선 일부 None 가능)
    try:
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu = psutil.cpu_percent(interval=0.0)  # 즉시 샘플
    except Exception:
        mem = disk = None
        cpu = None

    overall_ok = db_ok
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if overall_ok else "unhealthy",
        "timestamp": _now_iso(),
        "service": "clean-fastapi",
        "version": settings.APP_VERSION,
        "database": {"status": db_status},
        "system": {
            "cpu_percent": cpu,
            "memory": {
                "total": getattr(mem, "total", None),
                "available": getattr(mem, "available", None),
                "percent": getattr(mem, "percent", None),
            } if mem else None,
            "disk": {
                "total": getattr(disk, "total", None),
                "free": getattr(disk, "free", None),
                "percent": getattr(disk, "percent", None),
            } if disk else None,
        },
        "environment": {
            "python_version": os.sys.version.split(" ")[0],
            "environment": infrastructure_settings.ENVIRONMENT,
        },
    }


@router.get("/ready")
async def readiness_check(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Readiness(준비 상태): 트래픽 수신 “준비 완료” 여부.
    - 여기서는 Postgres + RabbitMQ 모두 연결 가능한지를 확인.
    - 둘 중 하나라도 실패하면 503을 반환 → 서비스로 트래픽 유입 차단.
    - 타임아웃은 짧게(기본 1초) 잡아 빠르게 실패하되, 재시도는 k8s가 하도록.
    """
    _no_store_headers(response)

    tasks = []

    # Postgres 체크
    tasks.append(_db_ping(db, timeout_s=1.0))

    # RabbitMQ 체크 (설정에서 URL 가져오기)
    rabbit_url = infrastructure_settings.RABBITMQ_URL
    rabbit_status = None
    rabbit_ok = True  # 미설정 시에는 OK로 간주(선택 사항)
    if rabbit_url:
        tasks.append(_rabbitmq_ping(rabbit_url, timeout_s=1.0))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 해석
    db_ok, db_err = results[0] if isinstance(results[0], tuple) else (False, str(results[0]))

    if rabbit_url:
        # RabbitMQ 결과가 두 번째
        r = results[1]
        if isinstance(r, tuple):
            rabbit_ok, rabbit_err = r
            rabbit_status = "healthy" if rabbit_ok else f"unhealthy: {rabbit_err}"
        else:
            rabbit_ok = False
            rabbit_status = f"unhealthy: {r!s}"
    else:
        rabbit_status = "skipped"  # 설정이 없으면 체크 스킵

    overall_ok = db_ok and rabbit_ok
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if overall_ok else "not_ready",
        "timestamp": _now_iso(),
        "dependencies": {
            "postgres": "healthy" if db_ok else f"unhealthy: {db_err}",
            "rabbitmq": rabbit_status,
        },
    }


@router.get("/live")
async def liveness_check(response: Response):
    """
    Liveness(생존 상태): 프로세스가 살아있는지만 확인(의존성 체크 X).
    - 애플리케이션 루프/프로세스가 동작 중이면 OK.
    - 의존성 장애로 재시작 루프에 빠지지 않도록 Readiness와 분리하는 것이 베스트 프랙티스.
    """
    _no_store_headers(response)
    return {"status": "alive", "timestamp": _now_iso()}
