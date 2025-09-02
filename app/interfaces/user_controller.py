from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel  
from app.application.services.user_service import UserService
from app.schemas.user_request import CreateUserBody, UpdateUserBody
from app.schemas.user_response import UserResponse
from typing import Optional
from datetime import datetime
from app.common.security import CurrentUser, get_current_user, get_admin_user
from dependency_injector.wiring import inject, Provide
from app.container import Container

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", status_code=201)
@inject
async def create_user(
    body: CreateUserBody,
    user_service: UserService = Depends(Provide[Container.user_service]),
    ):

    user = await user_service.create_user(
        body.name,
        body.email,
        body.password,
    )
    return UserResponse.from_domain(user)

@router.get("", status_code=200)
@inject
async def list_users(
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = None,
    user_service: UserService = Depends(Provide[Container.user_service]),  
):
    cursor_created_at, cursor_id = None, None
    if cursor:
        # cursor 파싱
        parts = cursor.split("_")
        cursor_created_at = datetime.fromisoformat(parts[0])
        cursor_id = parts[1]

    users, next_cursor = await user_service.list_users(limit, cursor_created_at, cursor_id)
    return {"users": UserResponse.list_from_domain(users), "next_cursor": next_cursor}


@router.put("", response_model=UserResponse, status_code=200)
@inject
async def update_user(
    body: UpdateUserBody,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(Provide[Container.user_service]),
):

    user = await user_service.update_user(
        body.email,
        body.current_password,
        body.new_password,
        body.new_name,
        body.new_memo,
        body.new_role,
    )
    return UserResponse.from_domain(user)


@router.delete("/{user_id}", status_code=204)
@inject
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_admin_user),
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")