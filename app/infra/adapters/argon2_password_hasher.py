from passlib.context import CryptContext
from app.application.ports.password_hasher import PasswordHasher

class Argon2PasswordHasher(PasswordHasher):
    def __init__(self):
        self._context = CryptContext(schemes=["argon2"], deprecated="auto")

    def encrypt(self, raw: str) -> str:
        return self._context.hash(raw)

    def verify(self, raw: str, hashed: str) -> bool:
        return self._context.verify(raw, hashed)
