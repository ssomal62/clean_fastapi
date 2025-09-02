from utils.crypto import Crypto
from passlib.context import CryptContext

class Crypto:
    def __init__(self):
        self.password_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def encrypt(self, password: str) -> str:
        return self.password_context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        return self.password_context.verify(password, hashed)

crypto = Crypto()