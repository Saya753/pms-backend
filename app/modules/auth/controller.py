from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from datetime import datetime, timezone

from app.database.session import get_db
from app.modules.users.services import UserService
from app.core.dependencies import get_current_user, get_refresh_token, get_refresh_token_credentials
from app.core.security import (
    create_access_token,
    create_refresh_token_data,
    hash_refresh_token,
)
from app.modules.users.models import User
from app.modules.users.repositories import UserRepository

from app.modules.auth.repositories import RefreshTokenRepository
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
    
    
# @auth_router.post("/refresh", response_model=LoginResponse)
# async def refresh_token(
#     user_id: Annotated[
#         int,
#         Depends(get_refresh_token),
#     ],
#     db: Annotated[
#         AsyncSession,
#         Depends(get_db),
#     ],
# ):
#     repository = UserRepository(db)

#     user = await repository.get_by_id(user_id)

#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="User not found",
#         )

#     if not user.status:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="User account is inactive",
#         )

#     new_access_token = create_access_token(user.id)
#     new_refresh_token = create_refresh_token(user.id)

#     return LoginResponse(
#         access_token=new_access_token,
#         refresh_token=new_refresh_token,
#         token_type="bearer",
#     )
    
    
@auth_router.post(
    "/refresh",
    response_model=LoginResponse,
)
async def refresh_token(
    refresh_data: Annotated[
        dict,
        Depends(get_refresh_token),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    user_id = refresh_data["user_id"]
    jti = refresh_data["jti"]
    token = refresh_data["token"]

    # -------------------------
    # Get user
    # -------------------------

    user_repository = UserRepository(db)

    user = await user_repository.get_by_id(user_id)

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

    # -------------------------
    # Get refresh token
    # -------------------------

    refresh_repository = RefreshTokenRepository(db)

    stored_token = await refresh_repository.get_by_jti(jti)

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    # -------------------------
    # Check revoked
    # -------------------------

    if stored_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    # -------------------------
    # Check expiration
    # -------------------------

    if stored_token.expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # -------------------------
    # Check token hash
    # -------------------------

    if stored_token.token_hash != hash_refresh_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # -------------------------
    # Revoke old token
    # -------------------------

    await refresh_repository.revoke(stored_token)

    # -------------------------
    # Create new tokens
    # -------------------------

    new_access_token = create_access_token(user.id)

    new_refresh_data = create_refresh_token_data(user.id)

    # -------------------------
    # Save new refresh token
    # -------------------------

    await refresh_repository.create(
        user_id=user.id,
        jti=new_refresh_data["jti"],
        token_hash=hash_refresh_token(
            new_refresh_data["token"]
        ),
        expires_at=new_refresh_data["expires_at"],
    )

    # -------------------------
    # Commit transaction
    # -------------------------

    await db.commit()

    return LoginResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_data["token"],
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