from datetime import datetime
from typing import Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from .mapper import user_to_response, users_to_response
from ..dtos import CreateUserBody, UpdateUserBody, UserResponse  
from ...src.user.service import UserService
from ...src.infrastructure.jwt_provider import CurrentUser, get_current_user_from_token
from ...src.shared.exceptions import NotFoundException
from ..container import MainContainer

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", status_code=201)
@inject
async def create_user(
    body: CreateUserBody,
    user_service: UserService = Depends(Provide[MainContainer.user_service]),
    ):

    user = await user_service.create_user(
        body.name,
        body.email,
        body.password,
    )
    return user_to_response(user)

@router.get("", status_code=200)
@inject
async def list_users(
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = None,
    user_service: UserService = Depends(Provide[MainContainer.user_service]),
):
    cursor_created_at, cursor_id = None, None
    if cursor:
        # cursor 파싱
        parts = cursor.split("_")
        cursor_created_at = datetime.fromisoformat(parts[0])
        cursor_id = parts[1]

    users, next_cursor = await user_service.list_users(limit, cursor_created_at, cursor_id)
    return users_to_response(users, next_cursor)


@router.put("", response_model=UserResponse, status_code=200)
@inject
async def update_user(
    body: UpdateUserBody,
    current_user: CurrentUser = Depends(get_current_user_from_token),
    user_service: UserService = Depends(Provide[MainContainer.user_service]),
):

    user = await user_service.update_user(
        body.email,
        body.current_password,
        body.new_password,
        body.new_name,
        body.new_memo,
        body.new_role,
    )
    return user_to_response(user)


@router.delete("/{user_id}", status_code=204)
@inject
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(Provide[MainContainer.get_admin_user]),
    user_service: UserService = Depends(Provide[MainContainer.user_service]),
):
    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise NotFoundException(resource="User", resource_id=user_id)