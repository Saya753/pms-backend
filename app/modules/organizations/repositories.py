from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import (
    Organization,
    OrganizationMember,
    Role,
)


class OrganizationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization: Organization,
    ) -> Organization:

        self.db.add(organization)

        await self.db.flush()
        await self.db.refresh(organization)

        return organization

    async def get_by_id(
        self,
        organization_id: int,
    ) -> Organization | None:

        result = await self.db.execute(
            select(Organization).where(
                Organization.id == organization_id
            )
        )

        return result.scalar_one_or_none()

    async def get_user_organizations(
        self,
        user_id: int,
    ) -> list[Organization]:

        result = await self.db.execute(
            select(Organization)
            .join(
                OrganizationMember,
                OrganizationMember.organization_id
                == Organization.id,
            )
            .where(
                OrganizationMember.user_id == user_id
            )
        )

        return list(result.scalars().all())
    
    
    async def get_role_by_name(
        self,
        role_name: str,
    ) -> Role | None:

        result = await self.db.execute(
            select(Role).where(
                Role.name == role_name
            )
        )

        return result.scalar_one_or_none()