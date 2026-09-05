from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.users.models import User

from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    InvitationCreate,
    OrganizationInvitationResponse,
    OrganizationMemberResponse,
    OrganizationMemberRoleUpdate,
    PendingInvitationCountResponse
)

from app.modules.organizations.services import (
    OrganizationService,
)


organization_router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
)

@organization_router.post(
    "",
    response_model=OrganizationResponse,
)
async def create_organization(

    data: OrganizationCreate,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.create(
        data=data,
        user_id=current_user.id,
    )
    
@organization_router.get(
    "",
    response_model=list[OrganizationResponse],
)
async def get_my_organizations(

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.get_my_organizations(
        current_user.id
    )
    
@organization_router.post(
    "/{organization_id}/invitations",
    response_model=OrganizationInvitationResponse,
)
async def invite_member(
    organization_id: int,

    data: InvitationCreate,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.invite_member(
        organization_id=organization_id,
        data=data,
        current_user_id=current_user.id,
    )
    
    
@organization_router.get(
    "/invitations",
    response_model=list[OrganizationInvitationResponse],
)
async def get_my_invitations(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.get_my_invitations(
        user_id=current_user.id
    )
    
@organization_router.post(
    "/invitations/{invitation_id}/accept",
    response_model=OrganizationInvitationResponse,
)
async def accept_invitation(
    invitation_id: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.accept_invitation(
        invitation_id=invitation_id,
        user_id=current_user.id,
    )
    
@organization_router.post(
    "/invitations/{invitation_id}/reject",
    response_model=OrganizationInvitationResponse,
)
async def reject_invitation(
    invitation_id: int,

    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],

    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.reject_invitation(
        invitation_id=invitation_id,
        user_id=current_user.id,
    )
    
@organization_router.get(
    "/{organization_id}/members",
    response_model=list[OrganizationMemberResponse],
)
async def get_organization_members(
    organization_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = OrganizationService(db)

    return await service.get_organization_members(
        organization_id=organization_id,
        current_user_id=current_user.id,
    )
    
@organization_router.delete(
    "/{organization_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_organization_member(
    organization_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = OrganizationService(db)

    await service.remove_member(
        organization_id=organization_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )
    
@organization_router.patch(
    "/{organization_id}/members/{user_id}/role",
    response_model=OrganizationMemberResponse,
)
async def update_organization_member_role(
    organization_id: int,
    user_id: int,
    data: OrganizationMemberRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = OrganizationService(db)

    return await service.update_member_role(
        organization_id=organization_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        role_name=data.role,
    )
    
@organization_router.get(
    "/users/me/invitations/pending-count",
    response_model=PendingInvitationCountResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pending_invitation_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = OrganizationService(db)

    count = await service.get_pending_invitation_count(
        current_user_id=current_user.id,
    )

    return {
        "count": count,
    }