from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from ..shared.exceptions import ForbiddenException, UnauthorizedException

# OAuth2 스키마 정의
security = OAuth2PasswordBearer(tokenUrl="/auth/login")

@dataclass
class CurrentUser:
    id: str
    role: str


class JwtProvider:
    def __init__(
        self, 
        secret_key: str, 
        algorithm: str, 
        access_token_expire_minutes: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, data: dict, role: str, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=self.access_token_expire_minutes))
        to_encode.update({
            "exp": int(expire.timestamp()),
            "role": role,
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise UnauthorizedException("Token has expired")
        except InvalidTokenError:
            raise UnauthorizedException("Invalid Token")

    def get_current_user(self, token: str) -> CurrentUser:
        payload = self.decode_access_token(token)
        user_id = payload.get("sub")
        role = payload.get("role")

        if not user_id or not role:
            raise ForbiddenException("Invalid credentials")

        return CurrentUser(user_id, role)

    def get_admin_user(self, token: str) -> CurrentUser:
        payload = self.decode_access_token(token)
        role = payload.get("role")
        if not role or role != "admin":
            raise ForbiddenException("Invalid credentials")
        return CurrentUser("ADMIN_USER_ID", role)


# FastAPI OAuth2와 호환되는 함수들
def get_current_user_from_token(token: str = Depends(security)) -> CurrentUser:
    """OAuth2 토큰에서 현재 사용자 정보를 가져옵니다."""
    from ...webapp.container import MainContainer
    container = MainContainer()
    jwt_provider = container.infrastructure.jwt_provider()
    return jwt_provider.get_current_user(token)


def get_admin_user_from_token(token: str = Depends(security)) -> CurrentUser:
    """OAuth2 토큰에서 관리자 사용자 정보를 가져옵니다."""
    from ...webapp.container import MainContainer
    container = MainContainer()
    jwt_provider = container.infrastructure.jwt_provider()
    return jwt_provider.get_admin_user(token)




