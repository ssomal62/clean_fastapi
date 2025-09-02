# from fastapi import Depends
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database import get_db
# from app.application.services.auth_service import AuthService
# from app.infra.repositories.user_repository_sqlalchemy import SqlAlchemyUserRepository

# def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
#     repo = SqlAlchemyUserRepository(db)
#     return AuthService(repo)


# 컨테이너 주입으로 대체