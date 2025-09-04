from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from .container import MainContainer
from ..src.infrastructure.jwt_provider import JwtProvider, CurrentUser

# OAuth2 스키마 정의
security = OAuth2PasswordBearer(tokenUrl="/auth/login")

container = MainContainer()

def get_user_service():
    return container.user_service()

def get_note_service():
    return container.note.note_service()

def get_auth_service():
    return container.auth.auth_service()

def get_jwt_provider():
    return container.infrastructure.jwt_provider()

def get_current_user_from_token(token: str = Depends(security)) -> CurrentUser:
    """OAuth2 토큰에서 현재 사용자 정보를 가져옵니다."""
    jwt_provider = get_jwt_provider()
    return jwt_provider.get_current_user(token)

def get_admin_user_from_token(token: str = Depends(security)) -> CurrentUser:
    """OAuth2 토큰에서 관리자 사용자 정보를 가져옵니다."""
    jwt_provider = get_jwt_provider()
    return jwt_provider.get_admin_user(token)

