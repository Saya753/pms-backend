from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
)
from app.modules.projects.services import ProjectService, ProjectUpdate
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
    
@project_router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    organization_id: int,
    project_id: int,
    data: ProjectUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.update_project(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        data=data,
    )
    
@project_router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    organization_id: int,
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    await service.delete_project(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )
    
@project_router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    organization_id: int,
    project_id: int,
    data: ProjectMemberCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.add_project_member(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        data=data,
    )
    
@project_router.patch(
    "/{project_id}/members/{user_id}/role",
    response_model=ProjectMemberResponse,
)
async def update_project_member_role(
    organization_id: int,
    project_id: int,
    user_id: int,
    data: ProjectMemberRoleUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.update_project_member_role(
        organization_id=organization_id,
        project_id=project_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        data=data,
    )
    
@project_router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    organization_id: int,
    project_id: int,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    await service.remove_project_member(
        organization_id=organization_id,
        project_id=project_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )
    
@project_router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberResponse],
)
async def get_project_members(
    organization_id: int,
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = ProjectService(db)

    return await service.get_project_members(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )