from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.users.repositories import UserRepository
from app.modules.users.schemas import UserRegister

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

class UserService:

    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def register(
        self,
        data: UserRegister,
    ) -> User:

        existing_email = await self.repository.get_by_email(
            data.email
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        existing_username = await self.repository.get_by_username(
            data.username
        )

        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already registered",
            )

        existing_phone = await self.repository.get_by_phone(
            data.phone
        )

        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone already registered",
            )

        user = User(
            full_name=data.full_name,
            username=data.username,
            phone=data.phone,
            email=data.email,
            hashed_password=hash_password(data.password),
        )

        return await self.repository.create(user)
    
    async def login(
        self,
        email: str,
        password: str,
    ) -> dict:

        user = await self.repository.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        access_token = create_access_token(user.id)

        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }