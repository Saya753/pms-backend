from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshToken


class RefreshTokenRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def get_by_jti(
        self,
        jti: str,
    ) -> RefreshToken | None:

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.jti == jti
            )
        )

        return result.scalar_one_or_none()

    async def revoke(
        self,
        refresh_token: RefreshToken,
    ) -> None:

        refresh_token.revoked = True
        refresh_token.revoked_at = datetime.now(timezone.utc)

        await self.db.flush()