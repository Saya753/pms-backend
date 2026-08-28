from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.users.models import User

from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
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