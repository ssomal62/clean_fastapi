from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth_request import LoginBody
from app.schemas.auth_response import LoginResponse
from app.application.services.auth_service import AuthService
from app.interfaces.base_controller import BaseController

class AuthController(BaseController):
    """인증 도메인 컨트롤러"""

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        super().__init__()

    def register_routes(self) -> APIRouter:
        router = APIRouter(prefix="/auth", tags=["auth"])

        router.add_api_route(
            "/login",
            self.login,
            methods=["POST"],
            response_model=LoginResponse,
            summary="로그인",
            description="이메일/비밀번호로 로그인하여 JWT 토큰 발급합니다.",
        )

        return router

    async def login(
        self, 
        form_data: OAuth2PasswordRequestForm = Depends(),
        ) -> LoginResponse:
        """로그인"""
        access_token = await self.auth_service.login(
            email=form_data.username,
            password=form_data.password,
            )
        return LoginResponse(access_token=access_token, token_type="Bearer")