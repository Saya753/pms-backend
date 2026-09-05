from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.projects.schemas import (
    MyProjectResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
    ProjectMemberSearchResponse,
    ProjectResponse,
    ProjectUpdate,
)

from app.modules.projects.services import ProjectService
from app.modules.users.models import User


# =========================================================
# ROUTERS
# =========================================================

project_router = APIRouter(
    prefix="/organizations/{organization_id}/projects",
    tags=["Projects"],
)

my_project_router = APIRouter(
    prefix="/users/me/projects",
    tags=["My Projects"],
)


# =========================================================
# CREATE PROJECT
# =========================================================

@project_router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    organization_id: int,
    data: ProjectCreate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.create_project(
        organization_id=organization_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# GET ORGANIZATION PROJECTS
# =========================================================

@project_router.get(
    "",
    response_model=list[ProjectListResponse],
)
async def get_organization_projects(
    organization_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
):
    service = ProjectService(db)

    return await service.get_organization_projects(
        organization_id=organization_id,
        current_user_id=current_user.id,
        search=search,
        status_filter=status_filter,
    )


# =========================================================
# PROJECT DETAIL
# =========================================================

@project_router.get(
    "/{project_id}/details",
    response_model=ProjectDetailResponse,
)
async def get_project_detail(
    organization_id: int,
    project_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.get_project_detail(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )


# =========================================================
# UPDATE PROJECT
# =========================================================

@project_router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    organization_id: int,
    project_id: int,
    data: ProjectUpdate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.update_project(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# DELETE PROJECT
# =========================================================

@project_router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    organization_id: int,
    project_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    await service.delete_project(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )


# =========================================================
# SEARCH ORGANIZATION MEMBERS
# =========================================================
# IMPORTANT:
# This route is defined before /{project_id}/members
# to keep the routing explicit and avoid ambiguity.

@project_router.get(
    "/members/search",
    response_model=list[ProjectMemberSearchResponse],
)
async def search_organization_members(
    organization_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    search: str = Query(
        min_length=2,
        max_length=50,
    ),
):
    service = ProjectService(db)

    return await service.search_organization_members(
        organization_id=organization_id,
        current_user_id=current_user.id,
        search=search,
    )


# =========================================================
# ADD PROJECT MEMBER
# =========================================================

@project_router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    organization_id: int,
    project_id: int,
    data: ProjectMemberCreate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.add_project_member(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# UPDATE PROJECT MEMBER ROLE
# =========================================================

@project_router.patch(
    "/{project_id}/members/{user_id}/role",
    response_model=ProjectMemberResponse,
)
async def update_project_member_role(
    organization_id: int,
    project_id: int,
    user_id: int,
    data: ProjectMemberRoleUpdate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.update_project_member_role(
        organization_id=organization_id,
        project_id=project_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# REMOVE PROJECT MEMBER
# =========================================================

@project_router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    organization_id: int,
    project_id: int,
    user_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    await service.remove_project_member(
        organization_id=organization_id,
        project_id=project_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
    )


# =========================================================
# GET PROJECT MEMBERS
# =========================================================

@project_router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberResponse],
)
async def get_project_members(
    organization_id: int,
    project_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = ProjectService(db)

    return await service.get_project_members(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )


# =========================================================
# MY PROJECTS
# =========================================================

@my_project_router.get(
    "",
    response_model=list[MyProjectResponse],
)
async def get_my_projects(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    organization_id: int | None = None,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
):
    service = ProjectService(db)

    return await service.get_user_projects(
        user_id=current_user.id,
        search=search,
        organization_id=organization_id,
        status_filter=status_filter,
    )


# =========================================================
# ALL VISIBLE PROJECTS
# =========================================================

@my_project_router.get(
    "/visible",
    response_model=list[ProjectListResponse],
)
async def get_visible_projects(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    organization_id: int | None = None,
    status_filter: str | None = Query(
        default=None,
        alias="status",
    ),
):
    service = ProjectService(db)

    return await service.get_visible_projects(
        current_user_id=current_user.id,
        organization_id=organization_id,
        search=search,
        status_filter=status_filter,
    )