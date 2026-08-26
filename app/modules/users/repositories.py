from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken

class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
            self,
            user_id: int,
        ) -> User | None:

            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )

            return result.scalar_one_or_none()
        
    async def get_by_email(
        self,
        email: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(User.email == email)
        )

        return result.scalar_one_or_none()

    async def get_by_username(
        self,
        username: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(User.username == username)
        )

        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        phone: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(User.phone == phone)
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        jti: str,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:

        refresh_token = RefreshToken(
            user_id=user_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(refresh_token)

        await self.db.flush()
        await self.db.refresh(refresh_token)

        return refresh_token
