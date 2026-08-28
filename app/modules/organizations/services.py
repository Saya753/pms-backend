from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import (
    Organization,
    OrganizationMember,
    Role,
)
from app.modules.organizations.repositories import (
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    OrganizationCreate,
)


class OrganizationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrganizationRepository(db)

    async def create(
        self,
        data: OrganizationCreate,
        user_id: int,
    ) -> Organization:

        owner_role = await self.repository.get_role_by_name(
            "OWNER"
        )

        if not owner_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OWNER role not found",
            )

        try:
            organization = Organization(
                name=data.name,
                description=data.description,
                owner_id=user_id,
            )

            self.db.add(organization)

            await self.db.flush()

            member = OrganizationMember(
                organization_id=organization.id,
                user_id=user_id,
                role_id=owner_role.id,
            )

            self.db.add(member)

            await self.db.commit()

            await self.db.refresh(organization)

            return organization

        except Exception:
            await self.db.rollback()
            raise
        
    async def get_my_organizations(
        self,
        user_id: int,
    ) -> list[Organization]:

        return await self.repository.get_user_organizations(
            user_id
        )