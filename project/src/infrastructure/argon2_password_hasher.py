from passlib.context import CryptContext
from passlib.exc import PasswordSizeError, TokenError

from ..shared.exceptions import ValidationException


class Argon2PasswordHasher:
    def __init__(self):
        self._context = CryptContext(schemes=["argon2"], deprecated="auto")

    def encrypt(self, raw: str) -> str:
        try:
            return self._context.hash(raw)
        except PasswordSizeError as e:
            raise ValidationException(f"Password size error: {str(e)}")
        except Exception as e:
            raise ValidationException(f"Password encryption failed: {str(e)}")

    def verify(self, raw: str, hashed: str) -> bool:
        try:
            return self._context.verify(raw, hashed)
        except TokenError as e:
            raise ValidationException(f"Invalid password hash format: {str(e)}")
        except Exception as e:
            raise ValidationException(f"Password verification failed: {str(e)}")


# PasswordHasher 별칭
PasswordHasher = Argon2PasswordHasher
