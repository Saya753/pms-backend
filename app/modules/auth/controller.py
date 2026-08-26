from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database.session import get_db
from app.modules.users.services import UserService
from app.core.dependencies import get_current_user, get_refresh_token, get_refresh_token_credentials
from app.core.security import create_access_token, create_refresh_token
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    LogoutRequest,
    LogoutResponse
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
    
    
@auth_router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    user_id: Annotated[
        int,
        Depends(get_refresh_token),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    repository = UserRepository(db)

    user = await repository.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
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


# @auth_router.post(
#     "/logout",
#     response_model=LogoutResponse,
# )
# async def logout(
#     data: LogoutRequest,
# ):
#     return LogoutResponse(
#         message="Successfully logged out",
#     )

@auth_router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    refresh_token: Annotated[
        str,
        Depends(get_refresh_token_credentials),
    ],
):
    return LogoutResponse(
        message="Successfully logged out",
    )