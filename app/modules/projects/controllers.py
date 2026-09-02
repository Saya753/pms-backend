from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectResponse,
)
from app.modules.projects.services import ProjectService
from app.modules.users.models import User


project_router = APIRouter(
    prefix="/organizations/{organization_id}/projects",
    tags=["Projects"],
)


@project_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    organization_id: int,
    data: ProjectCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.create_project(
        organization_id=organization_id,
        current_user_id=current_user.id,
        data=data,
    )
    
@project_router.get(
    "",
    response_model=list[ProjectResponse],
)
async def get_organization_projects(
    organization_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.get_organization_projects(
        organization_id=organization_id,
        current_user_id=current_user.id,
    )