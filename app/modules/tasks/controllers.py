from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.tasks.schemas import (
    TaskAssign,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    MyTaskUpdate,
)
from app.modules.tasks.services import TaskService

from app.modules.users.models import User


task_router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks",
    tags=["Tasks"],
)


my_task_router = APIRouter(
    prefix="/users/me/tasks",
    tags=["My Tasks"],
)


# =========================================================
# CREATE TASK
# =========================================================

@task_router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    organization_id: int,
    project_id: int,
    data: TaskCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.create_task(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# LIST PROJECT TASKS
# =========================================================

@task_router.get(
    "",
    response_model=list[TaskResponse],
)
async def get_project_tasks(
    organization_id: int,
    project_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.get_project_tasks(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )


# =========================================================
# GET TASK DETAILS
# =========================================================

@task_router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
async def get_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.get_task(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


# =========================================================
# UPDATE TASK
# =========================================================

@task_router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.update_task(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# ASSIGN TASK
# =========================================================

@task_router.patch(
    "/{task_id}/assign",
    response_model=TaskResponse,
)
async def assign_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    data: TaskAssign,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.assign_task(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# DELETE TASK
# =========================================================

@task_router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    organization_id: int,
    project_id: int,
    task_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    await service.delete_task(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


# =========================================================
# MY TASKS
# =========================================================

@my_task_router.get(
    "",
    response_model=list[TaskResponse],
)
async def get_my_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.get_my_tasks(
        current_user_id=current_user.id,
    )
    
@my_task_router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_my_task(
    task_id: int,
    data: MyTaskUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = TaskService(db)

    return await service.update_my_task(
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )