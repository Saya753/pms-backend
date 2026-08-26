from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

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
        user: User,
    ) -> User:

        self.db.add(user)

        await self.db.commit()

        await self.db.refresh(user)

        return user