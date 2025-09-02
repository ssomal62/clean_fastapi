from fastapi import APIRouter
from abc import abstractmethod

class BaseController:
    """모든 컨트롤러의 베이스 클래스"""
    
    def __init__(self):
        self.router = self.register_routes()
    
    @abstractmethod
    def register_routes(self) -> APIRouter:
        """각 컨트롤러에서 라우트 설정"""
        pass