from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.repositories import NotificationRepository

from app.modules.organizations.models import (
    Organization,
    OrganizationInvitation,
    OrganizationMember,
)
from app.modules.organizations.repositories import (
    OrganizationRepository,
)
from app.modules.organizations.schemas import (
    InvitationCreate,
    OrganizationCreate,
    OrganizationUpdate,
)


class OrganizationService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = OrganizationRepository(db)
        self.notification_repository = NotificationRepository(db)

    # =========================================================
    # Helpers
    # =========================================================

    async def _require_permission(
        self,
        organization_id: int,
        user_id: int,
        permission_name: str,
        detail: str,
    ) -> None:

        has_permission = await self.repository.member_has_permission(
            organization_id=organization_id,
            user_id=user_id,
            permission_name=permission_name,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail,
            )

    async def _require_membership(
        self,
        organization_id: int,
        user_id: int,
    ) -> OrganizationMember:

        member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=user_id,
        )

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
            )

        return member

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

    # =========================================================
    # Create Organization
    # =========================================================

    async def create(
        self,
        data: OrganizationCreate,
        user_id: int,
    ) -> Organization:

        owner_role = await self.repository.get_role_by_name("OWNER")

        if not owner_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OWNER role not found",
            )

        try:
            organization = Organization(
                name=data.name.strip(),
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

    # =========================================================
    # Get My Organizations
    # =========================================================

    async def get_my_organizations(
        self,
        user_id: int,
    ) -> list[Organization]:

        return await self.repository.get_user_organizations(
            user_id
        )

    # =========================================================
    # Get Organization Detail
    # =========================================================

    async def get_organization(
        self,
        organization_id: int,
        current_user_id: int,
    ) -> Organization:

        organization = await self.repository.get_organization(
            organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self._require_membership(
            organization_id=organization_id,
            user_id=current_user_id,
        )

        return organization

    # =========================================================
    # Update Organization
    # =========================================================

    async def update_organization(
        self,
        organization_id: int,
        data: OrganizationUpdate,
        current_user_id: int,
    ) -> Organization:

        organization = await self.repository.get_organization(
            organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self._require_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="organization.update",
            detail="You do not have permission to update this organization",
        )

        if data.name is None and data.description is None:
            return organization

        try:
            organization = await self.repository.update(
                organization=organization,
                name=data.name.strip() if data.name is not None else None,
                description=data.description,
            )

            await self.db.commit()
            await self.db.refresh(organization)

            return organization

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Invite Member
    # =========================================================

    async def invite_member(
        self,
        organization_id: int,
        data: InvitationCreate,
        current_user_id: int,
    ):

        await self._require_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.invite",
            detail="You do not have permission to invite members",
        )

        organization = await self.repository.get_organization(
            organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        invited_user = await self.repository.get_user_by_username(
            data.username.strip()
        )

        if not invited_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if invited_user.id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot invite yourself",
            )

        inviter = await self.repository.get_user_by_id(
            current_user_id
        )

        if not inviter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inviter not found",
            )

        existing_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=invited_user.id,
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization",
            )

        existing_invitation = await self.repository.get_pending_invitation(
            organization_id=organization_id,
            invited_user_id=invited_user.id,
        )

        if existing_invitation:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A pending invitation already exists",
            )

        role = await self.repository.get_role_by_name(
            data.role
        )

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

        try:
            invitation = await self.repository.create_invitation(
                organization_id=organization_id,
                invited_user_id=invited_user.id,
                invited_by=current_user_id,
                role_id=role.id,
            )

            inviter_name = (
                inviter.full_name
                if inviter.full_name
                else "Unknown User"
            )

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
                    f'"{organization.name}" دعوت کرده است.'
                ),
            )

            await self.db.commit()

            return await self._build_invitation_response(
                invitation
            )

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Get My Invitations
    # =========================================================

    async def get_my_invitations(
        self,
        current_user_id: int,
    ):

        invitations = await self.repository.get_my_invitations(
            user_id=current_user_id
        )

        result = []

        for invitation in invitations:

            # اگر دعوتنامه تاریخ انقضا داشته باشد
            if invitation.expires_at:
                now = datetime.now(timezone.utc)

                if invitation.expires_at <= now:
                    await self.repository.update_invitation(
                        invitation,
                        "EXPIRED",
                    )
                    continue

            result.append(
                await self._build_invitation_response(
                    invitation
                )
            )

        # اگر invitationهای expired تغییر کرده باشند
        if any(
            invitation.expires_at
            and invitation.expires_at <= datetime.now(timezone.utc)
            for invitation in invitations
        ):
            await self.db.commit()

        return result

    # =========================================================
    # Accept Invitation
    # =========================================================

    async def accept_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ):

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

        try:
            await self.repository.create_member(
                organization_id=invitation.organization_id,
                user_id=user_id,
                role_id=invitation.role_id,
            )

            await self.repository.update_invitation(
                invitation,
                "ACCEPTED",
            )

            notification = (
                await self.notification_repository
                .get_notification_by_invitation(
                    invitation_id=invitation.id,
                    user_id=user_id,
                )
            )

            if notification:
                await self.notification_repository.mark_as_read(
                    notification
                )

            await self.db.commit()

            return await self._build_invitation_response(
                invitation
            )

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Reject Invitation
    # =========================================================

    async def reject_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ):

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

        try:
            await self.repository.update_invitation(
                invitation,
                "REJECTED",
            )

            notification = (
                await self.notification_repository
                .get_notification_by_invitation(
                    invitation_id=invitation.id,
                    user_id=user_id,
                )
            )

            if notification:
                await self.notification_repository.mark_as_read(
                    notification
                )

            await self.db.commit()

            return await self._build_invitation_response(
                invitation
            )

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Get Organization Members
    # =========================================================

    async def get_organization_members(
        self,
        organization_id: int,
        current_user_id: int,
    ) -> list[dict]:

        organization = await self.repository.get_organization(
            organization_id
        )

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self._require_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.read",
            detail="You do not have permission to view organization members",
        )

        return await self.repository.get_organization_members(
            organization_id=organization_id
        )

    # =========================================================
    # Remove Member
    # =========================================================

    async def remove_member(
        self,
        organization_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> None:

        await self._require_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="member.remove",
            detail="You do not have permission to remove members",
        )

        target_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=target_user_id,
        )

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this organization",
            )

        target_role = await self.repository.get_role_by_id(
            target_member.role_id
        )

        if not target_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member role not found",
            )

        if target_role.name == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The organization owner cannot be removed",
            )

        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove yourself from the organization",
            )

        try:
            await self.repository.delete_member(
                target_member
            )

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Update Member Role
    # =========================================================

    async def update_member_role(
        self,
        organization_id: int,
        target_user_id: int,
        current_user_id: int,
        role_name: str,
    ) -> OrganizationMember:

        await self._require_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="role.manage",
            detail="You do not have permission to manage organization roles",
        )

        current_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=current_user_id,
        )

        if not current_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
            )

        target_member = await self.repository.get_member(
            organization_id=organization_id,
            user_id=target_user_id,
        )

        if not target_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in this organization",
            )

        if target_user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role",
            )

        target_role = await self.repository.get_role_by_id(
            target_member.role_id
        )

        if target_role and target_role.name == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The organization owner role cannot be changed",
            )

        role = await self.repository.get_role_by_name(
            role_name
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        if role.name == "OWNER":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot assign the OWNER role",
            )

        if role.name not in {"ADMIN", "MEMBER"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization role",
            )

        try:
            updated_member = await self.repository.update_member_role(
                member=target_member,
                role_id=role.id,
            )

            await self.db.commit()
            await self.db.refresh(updated_member)

            return updated_member

        except Exception:
            await self.db.rollback()
            raise

    # =========================================================
    # Pending Invitation Count
    # =========================================================

    async def get_pending_invitation_count(
        self,
        current_user_id: int,
    ) -> int:

        return await self.repository.get_pending_invitation_count(
            user_id=current_user_id
        )

    # =========================================================
    # Delete Organization
    # =========================================================

    async def delete_organization(
        self,
        organization_id: int,
        current_user_id: int,
    ):

        organization = await self.repository.get_organization(
            organization_id
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