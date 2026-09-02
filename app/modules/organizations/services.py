from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.modules.organizations.models import (
    Organization,
    OrganizationMember,
    OrganizationInvitation,
    Role,
)

from app.modules.organizations.repositories import (
    OrganizationRepository,
)

from app.modules.organizations.schemas import (
    OrganizationCreate,
    InvitationCreate,
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
        
    async def invite_member(
        self,
        organization_id: int,
        data: InvitationCreate,
        current_user_id: int,
    ) -> OrganizationInvitation:

        # 1. بررسی Permission
        has_permission = await self.repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.invite",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to invite members",
            )

        # 2. پیدا کردن کاربر با username
        invited_user = await self.repository.get_user_by_username(
            data.username
        )

        if not invited_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 3. جلوگیری از دعوت خود کاربر
        if invited_user.id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot invite yourself",
            )

        # 4. بررسی عضویت قبلی
        existing_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=invited_user.id,
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )

        # 5. بررسی Invitation در وضعیت PENDING
        existing_invitation = (
            await self.repository.get_pending_invitation(
                organization_id=organization_id,
                invited_user_id=invited_user.id,
            )
        )

        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists",
            )

        # 6. بررسی Role
        role = await self.repository.get_role_by_name(data.role.upper())

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        allowed_organization_roles = {
            "ADMIN",
            "MEMBER",
        }

        if role.name not in allowed_organization_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization role",
            )

        # 7. ساخت Invitation
        invitation = await self.repository.create_invitation(
            organization_id=organization_id,
            invited_user_id=invited_user.id,
            invited_by=current_user_id,
            role_id=role.id,
        )

        await self.db.commit()

        await self.db.refresh(invitation)

        return invitation
    
    async def get_my_invitations(
        self,
        user_id: int,
    ) -> list[OrganizationInvitation]:

        return await self.repository.get_my_invitations(
            user_id=user_id
        )
        
    async def accept_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ) -> OrganizationInvitation:

        invitation = await self.repository.get_invitation(
            invitation_id
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.invited_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation does not belong to you",
            )

        if invitation.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer pending",
            )

        if invitation.expires_at:
            now = datetime.now(timezone.utc)

            if invitation.expires_at <= now:
                await self.repository.update_invitation(
                    invitation,
                    "EXPIRED",
                )

                await self.db.commit()

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation has expired",
                )

        existing_member = await self.repository.get_member(
            organization_id=invitation.organization_id,
            user_id=user_id,
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this organization",
            )

        await self.repository.create_member(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role_id=invitation.role_id,
        )

        await self.repository.update_invitation(
            invitation,
            "ACCEPTED",
        )

        await self.db.commit()

        return invitation
    
    async def reject_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ) -> OrganizationInvitation:

        invitation = await self.repository.get_invitation(
            invitation_id
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if invitation.invited_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation does not belong to you",
            )

        if invitation.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer pending",
            )

        await self.repository.update_invitation(
            invitation,
            "REJECTED",
        )

        await self.db.commit()

        return invitation
    
    async def get_organization_members(
        self,
        organization_id: int,
        current_user_id: int,
    ) -> list[OrganizationMember]:

        has_permission = await self.repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.read",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view organization members",
            )

        return await self.repository.get_organization_members(
            organization_id=organization_id
        )
        
    async def remove_member(
        self,
        organization_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> None:

        # 1. بررسی Permission
        has_permission = await self.repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.remove",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to remove members",
            )

        # 2. پیدا کردن عضو هدف
        target_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=target_user_id,
        )

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this organization",
            )

        # 3. گرفتن نقش عضو هدف
        target_role = await self.repository.get_role_by_id(
            target_member.role_id
        )

        if not target_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member role not found",
            )

        # 4. OWNER قابل حذف نیست
        if target_role.name == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The organization owner cannot be removed",
            )

        # 5. OWNER خودش هم از این endpoint حذف نشود
        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove yourself from the organization",
            )

        # 6. حذف عضو
        await self.repository.delete_member(target_member)

        await self.db.commit()