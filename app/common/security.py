from datetime import datetime, timedelta, UTC
from dataclasses import dataclass
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from app.core.config import settings
from app.domain.user import Role

@dataclass
class CurrentUser:
    id: str
    role: Role

#OAuth2PasswordBearer는 토큰을 검증하고 현재 사용자를 가져오는 데 사용되는 클래스
#tokenUrl은 실제 토큰 발급과 연결되지는 않고, 문서화 목적
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    return CurrentUser(user_id, Role(role))

def get_admin_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    payload = decode_access_token(token)

    role = payload.get("role")
    if not role or role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")
    
    return CurrentUser("ADMIN_USER_ID", Role(role))

def create_access_token(
    data: dict, 
    role: Role,
    expires_delta: timedelta | None = None
    ) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    to_encode.update({
        "exp": int(expire.timestamp()),
        "role": role,
        }) 
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
 