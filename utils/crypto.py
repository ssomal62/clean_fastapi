from passlib.hash import argon2

class Crypto:

    @staticmethod #=> 인스턴스 생성 안해도 바로 사용가능.
    def encrypt(password: str) -> str:
        # 평문 비밀번호를 Argon 2 해시로 변환
        return argon2.hash(password)

    @staticmethod
    def verify(password: str, hashed: str) -> bool:
        # 평문 비밀번호와 해시를 비교 검증
        return argon2.verify(password, hashed)

    