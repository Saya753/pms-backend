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
from app.modules.notifications.repositories import NotificationRepository


class OrganizationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrganizationRepository(db)
        self.notification_repository = NotificationRepository(db)

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
    # ---------------------------------------------------------
    # Invitation Response Helper
    # ---------------------------------------------------------

    async def _build_invitation_response(
        self,
        invitation: OrganizationInvitation,
    ) -> dict:

        organization = await self.repository.get_organization(
            invitation.organization_id
        )

        inviter = await self.repository.get_user_by_id(
            invitation.invited_by
        )

        return {
            "id": invitation.id,
            "organization_id": invitation.organization_id,
            "invited_user_id": invitation.invited_user_id,
            "invited_by": invitation.invited_by,
            "role": invitation.role,
            "status": invitation.status,
            "created_at": invitation.created_at,
            "expires_at": invitation.expires_at,
            "responded_at": invitation.responded_at,
            "organization_name": (
                organization.name
                if organization
                else "Unknown Organization"
            ),
            "inviter_name": (
                inviter.full_name
                if inviter and inviter.full_name
                else "Unknown User"
            ),
        }

    # ---------------------------------------------------------
    # Invite Member
    # ---------------------------------------------------------

    async def invite_member(
        self,
        organization_id: int,
        data: InvitationCreate,
        current_user_id: int,
    ):

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

        # 2. پیدا کردن Organization
        organization = await self.repository.get_organization(
            organization_id=organization_id,
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # 3. پیدا کردن کاربر با username
        invited_user = await self.repository.get_user_by_username(
            data.username
        )

        if not invited_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # 4. جلوگیری از دعوت خود کاربر
        if invited_user.id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot invite yourself",
            )

        # 5. پیدا کردن دعوت‌کننده
        inviter = await self.repository.get_user_by_id(
            current_user_id
        )

        if not inviter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inviter not found",
            )

        # 6. بررسی عضویت قبلی
        existing_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=invited_user.id,
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )

        # 7. بررسی Invitation قبلی در وضعیت PENDING
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

        # 8. پیدا کردن Role
        role = await self.repository.get_role_by_name(
            data.role.upper()
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        # فقط این Roleها برای Organization Invitation مجاز هستند
        allowed_organization_roles = {
            "ADMIN",
            "MEMBER",
        }

        if role.name not in allowed_organization_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization role",
            )

        # 9. ساخت Invitation
        invitation = await self.repository.create_invitation(
            organization_id=organization_id,
            invited_user_id=invited_user.id,
            invited_by=current_user_id,
            role_id=role.id,
        )

        # 10. ساخت Notification
        inviter_name = (
            inviter.full_name
            if inviter.full_name
            else "Unknown User"
        )

        organization_name = organization.name

        await self.notification_repository.create_notification(
            user_id=invited_user.id,
            organization_id=organization.id,
            project_id=None,
            task_id=None,
            invitation_id=invitation.id,
            notification_type="ORGANIZATION_INVITATION",
            title="دعوت‌نامه جدید",
            message=(
                f'{inviter_name} شما را به سازمان '
                f'"{organization_name}" دعوت کرده است.'
            ),
        )

        # 11. Response کامل
        return await self._build_invitation_response(
            invitation
        )

    # ---------------------------------------------------------
    # Get My Invitations
    # ---------------------------------------------------------

    async def get_my_invitations(
        self,
        current_user_id: int,
    ):

        invitations = await self.repository.get_my_invitations(
            user_id=current_user_id
        )

        result = []

        for invitation in invitations:

            invitation_response = (
                await self._build_invitation_response(
                    invitation
                )
            )

            result.append(invitation_response)

        return result

    # ---------------------------------------------------------
    # Accept Invitation
    # ---------------------------------------------------------

    async def accept_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ):

        # 1. پیدا کردن Invitation
        invitation = await self.repository.get_invitation(
            invitation_id
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        # 2. بررسی اینکه Invitation متعلق به همین User است
        if invitation.invited_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation does not belong to you",
            )

        # 3. فقط Invitationهای PENDING قابل قبول هستند
        if invitation.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer pending",
            )

        # 4. بررسی Expiration
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

        # 5. بررسی عضویت قبلی
        existing_member = await self.repository.get_member(
            organization_id=invitation.organization_id,
            user_id=user_id,
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this organization",
            )

        # 6. ساخت Organization Member
        await self.repository.create_member(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role_id=invitation.role_id,
        )

        # 7. تغییر وضعیت Invitation
        await self.repository.update_invitation(
            invitation,
            "ACCEPTED",
        )

        # 8. پیدا کردن Notification مربوط به Invitation
        notification = (
            await self.notification_repository
            .get_notification_by_invitation(
                invitation_id=invitation.id,
                user_id=user_id,
            )
        )

        # 9. Mark Notification as Read
        if notification:

            await self.notification_repository.mark_as_read(
                notification
            )

        # 10. Commit نهایی
        await self.db.commit()

        # 11. Response کامل
        return await self._build_invitation_response(
            invitation
        )

    # ---------------------------------------------------------
    # Reject Invitation
    # ---------------------------------------------------------

    async def reject_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ):

        # 1. پیدا کردن Invitation
        invitation = await self.repository.get_invitation(
            invitation_id
        )

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        # 2. بررسی مالکیت Invitation
        if invitation.invited_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This invitation does not belong to you",
            )

        # 3. بررسی وضعیت
        if invitation.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation is no longer pending",
            )

        # 4. تغییر وضعیت
        await self.repository.update_invitation(
            invitation,
            "REJECTED",
        )

        # 5. پیدا کردن Notification
        notification = (
            await self.notification_repository
            .get_notification_by_invitation(
                invitation_id=invitation.id,
                user_id=user_id,
            )
        )

        # 6. Mark Notification as Read
        if notification:

            await self.notification_repository.mark_as_read(
                notification
            )

        # 7. Commit نهایی
        await self.db.commit()

        # 8. Response کامل
        return await self._build_invitation_response(
            invitation
        )
            
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
        
    async def update_member_role(
        self,
        organization_id: int,
        target_user_id: int,
        current_user_id: int,
        role_name: str,
    ) -> OrganizationMember:

        # 1. فقط OWNER اجازه تغییر Role دارد
        current_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=current_user_id,
        )

        if not current_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
            )

        current_role = await self.repository.get_role_by_id(
            current_member.role_id
        )

        if not current_role or current_role.name != "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can change member roles",
            )

        # 2. عضو هدف را پیدا کن
        target_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=target_user_id,
        )

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this organization",
            )

        # 3. OWNER نمی‌تواند Role خودش را تغییر دهد
        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role",
            )

        # 4. Role مقصد را پیدا کن
        role = await self.repository.get_role_by_name(role_name)

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        # 5. هیچ عضوی از طریق این endpoint نمی‌تواند OWNER شود
        if role.name == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot assign the OWNER role",
            )

        # 6. تغییر Role
        updated_member = await self.repository.update_member_role(
            member=target_member,
            role_id=role.id,
        )

        await self.db.commit()
        await self.db.refresh(updated_member)

        return updated_member
    
    async def get_pending_invitation_count(
        self,
        current_user_id: int,
    ) -> int:

        return await self.repository.get_pending_invitation_count(
            user_id=current_user_id,
        )
        
    async def delete_organization(
        self,
        organization_id: int,
        current_user_id: int,
    ):
        organization = await self.repository.get_organization(
            organization_id=organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        if organization.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the organization owner can delete the organization",
            )

        await self.repository.delete_organization(
            organization
        )

        return {
            "message": "Organization deleted successfully"
        }