from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from sqlalchemy.orm import selectinload
from app.modules.users.models import User

from app.modules.organizations.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    Role,
    Permission,
    role_permissions,
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
    
    async def get_member(
        self,
        organization_id: int,
        user_id: int,
    ) -> OrganizationMember | None:

        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()
    
    async def get_user_by_username(
        self,
        username: str,
    ) -> User | None:

        result = await self.db.execute(
            select(User).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none()
    
    async def get_invitation(
        self,
        invitation_id: int,
    ) -> OrganizationInvitation | None:

        result = await self.db.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.id == invitation_id
            )
        )

        return result.scalar_one_or_none()
    
    async def get_pending_invitation(
        self,
        organization_id: int,
        invited_user_id: int,
    ) -> OrganizationInvitation | None:

        result = await self.db.execute(
            select(OrganizationInvitation).where(
                OrganizationInvitation.organization_id == organization_id,
                OrganizationInvitation.invited_user_id == invited_user_id,
                OrganizationInvitation.status == "PENDING",
            )
        )

        return result.scalar_one_or_none()
    
    async def create_invitation(
        self,
        organization_id: int,
        invited_user_id: int,
        invited_by: int,
        role_id: int,
    ) -> OrganizationInvitation:

        invitation = OrganizationInvitation(
            organization_id=organization_id,
            invited_user_id=invited_user_id,
            invited_by=invited_by,
            role_id=role_id,
            status="PENDING",
        )

        self.db.add(invitation)

        await self.db.flush()
        await self.db.refresh(invitation)

        return invitation
    
    # برای Accept/Reject استفاده می‌کنیم
    async def update_invitation(
        self,
        invitation: OrganizationInvitation,
        new_status: str,
    ) -> OrganizationInvitation:

        invitation.status = new_status
        invitation.responded_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(invitation)

        return invitation
    
    async def create_member(
        self,
        organization_id: int,
        user_id: int,
        role_id: int,
    ) -> OrganizationMember:

        member = OrganizationMember(
            organization_id=organization_id,
            user_id=user_id,
            role_id=role_id,
        )

        self.db.add(member)

        await self.db.flush()
        await self.db.refresh(member)

        return member
    
    
    async def member_has_permission(
        self,
        organization_id: int,
        user_id: int,
        permission_name: str,
    ) -> bool:

        result = await self.db.execute(
            select(OrganizationMember)
            .join(
                Role,
                OrganizationMember.role_id == Role.id,
            )
            .join(
                role_permissions,
                Role.id == role_permissions.c.role_id,
            )
            .join(
                Permission,
                role_permissions.c.permission_id == Permission.id,
            )
            .where(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_id,
                Permission.name == permission_name,
            )
        )

        return result.scalar_one_or_none() is not None

    async def get_permission_by_name(
        self,
        permission_name: str,
    ) -> Permission | None:

        result = await self.db.execute(
            select(Permission).where(
                Permission.name == permission_name
            )
        )

        return result.scalar_one_or_none()
    
    async def get_role_by_id(
        self,
        role_id: int,
    ) -> Role | None:

        result = await self.db.execute(
            select(Role).where(
                Role.id == role_id
            )
        )

        return result.scalar_one_or_none()
        
    async def get_my_invitations(
        self,
        user_id: int,
    ) -> list[OrganizationInvitation]:
        print("GETTING INVITATIONS FOR USER:", user_id)

        result = await self.db.execute(
            select(OrganizationInvitation)
            .options(
                selectinload(OrganizationInvitation.role),
            )
            .where(
                OrganizationInvitation.invited_user_id == user_id,
                OrganizationInvitation.status == "PENDING",
            )
            .order_by(OrganizationInvitation.created_at.desc())
        )

        invitations = list(result.scalars().all())

        print("FOUND INVITATIONS:", invitations)

        return invitations
    
    async def get_organization_members(
        self,
        organization_id: int,
    ):
        result = await self.db.execute(
            select(
                OrganizationMember,
                User.username,
                User.full_name,
            )
            .join(
                User,
                User.id == OrganizationMember.user_id,
            )
            .where(
                OrganizationMember.organization_id == organization_id
            )
        )

        rows = result.all()

        return [
            {
                "id": member.id,
                "organization_id": member.organization_id,
                "user_id": member.user_id,
                "username": username,
                "full_name": full_name,
                "role": member.role,
                "joined_at": member.joined_at,
            }
            for member, username, full_name in rows
        ]
        
    async def delete_member(
        self,
        member: OrganizationMember,
    ) -> None:
        await self.db.delete(member)
        
    async def update_member_role(
        self,
        member: OrganizationMember,
        role_id: int,
    ) -> OrganizationMember:

        member.role_id = role_id

        await self.db.flush()
        await self.db.refresh(member)

        return member
    
    async def get_pending_invitation_count(
        self,
        user_id: int,
    ) -> int:

        result = await self.db.execute(
            select(func.count(OrganizationInvitation.id))
            .where(
                OrganizationInvitation.invited_user_id == user_id,
                OrganizationInvitation.status == "PENDING",
            )
        )

        return result.scalar_one()
    
    async def get_organization(
        self,
        organization_id: int,
    ) -> Organization | None:

        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == organization_id)
        )

        return result.scalar_one_or_none()
    
    async def get_user_by_id(
        self,
        user_id: int,
    ) -> User | None:

        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
        )

        return result.scalar_one_or_none()
    
    async def get_organization(
        self,
        organization_id: int,
    ) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(
                Organization.id == organization_id
            )
        )
        return result.scalar_one_or_none()
    
    async def delete_organization(
        self,
        organization: Organization,
    ):
        await self.db.delete(organization)
        await self.db.commit()