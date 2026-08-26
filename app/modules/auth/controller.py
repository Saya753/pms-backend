from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database.session import get_db
from app.modules.users.services import UserService
from app.core.dependencies import get_current_user
from app.modules.users.models import User
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)


auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@auth_router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)

    user = await service.register(data)

    return user

@auth_router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)

    return await service.login(
        email=data.email,
        password=data.password,
    )
    
@auth_router.get(
    "/me",
    response_model=RegisterResponse,
)
async def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
):
    return current_user