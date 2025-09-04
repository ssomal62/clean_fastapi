from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from project.src.auth.service import AuthService
from ..dtos import LoginResponse
from ..container import MainContainer

from dependency_injector.wiring import Provide, inject

# 라우터 생성
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="로그인",
    description="이메일/비밀번호로 로그인하여 JWT 토큰 발급합니다.",
)
@inject
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(Provide[MainContainer.auth_service]),
) -> LoginResponse:
    """로그인"""
    access_token = await auth_service.login(
        email=form_data.username,
        password=form_data.password,
    )
    return LoginResponse(access_token=access_token, token_type="Bearer")