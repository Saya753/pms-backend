from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.tasks.schemas import (
    CheckpointCreate,
    CheckpointResponse,
    CheckpointUpdate,
    MyTaskUpdate,
    TaskAssign,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from app.modules.tasks.services import TaskService
from app.modules.users.models import User


# =========================================================
# TASK ROUTER
# =========================================================

task_router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks",
    tags=["Tasks"],
)


# =========================================================
# MY TASK ROUTER
# =========================================================

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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
    priority: str | None = Query(
        default=None,
        description="Filter tasks by priority",
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter tasks by status",
    ),
):
    service = TaskService(db)

    return await service.get_project_tasks(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
        priority=priority,
        status_filter=status_filter,
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
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
# PM / TEAM LEAD
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    await service.delete_task(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


# =========================================================
# GET SUBTASKS
# =========================================================

@task_router.get(
    "/{task_id}/subtasks",
    response_model=list[TaskResponse],
)
async def get_subtasks(
    organization_id: int,
    project_id: int,
    task_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.get_subtasks(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


# =========================================================
# CREATE SUBTASK
# =========================================================

@task_router.post(
    "/{task_id}/subtasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subtask(
    organization_id: int,
    project_id: int,
    task_id: int,
    data: TaskCreate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.create_subtask(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# GET CHECKPOINTS
# =========================================================

@task_router.get(
    "/{task_id}/checkpoints",
    response_model=list[CheckpointResponse],
)
async def get_checkpoints(
    organization_id: int,
    project_id: int,
    task_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.get_checkpoints(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


# =========================================================
# CREATE CHECKPOINT
# =========================================================

@task_router.post(
    "/{task_id}/checkpoints",
    response_model=CheckpointResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_checkpoint(
    organization_id: int,
    project_id: int,
    task_id: int,
    data: CheckpointCreate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.create_checkpoint(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# UPDATE CHECKPOINT
# =========================================================

@task_router.patch(
    "/{task_id}/checkpoints/{checkpoint_id}",
    response_model=CheckpointResponse,
)
async def update_checkpoint(
    organization_id: int,
    project_id: int,
    task_id: int,
    checkpoint_id: int,
    data: CheckpointUpdate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.update_checkpoint(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        checkpoint_id=checkpoint_id,
        current_user_id=current_user.id,
        data=data,
    )


# =========================================================
# DELETE CHECKPOINT
# =========================================================

@task_router.delete(
    "/{task_id}/checkpoints/{checkpoint_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_checkpoint(
    organization_id: int,
    project_id: int,
    task_id: int,
    checkpoint_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    await service.delete_checkpoint(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        checkpoint_id=checkpoint_id,
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
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.get_my_tasks(
        current_user_id=current_user.id,
    )


# =========================================================
# UPDATE MY TASK
# ONLY STATUS + PROGRESS
# =========================================================

@my_task_router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_my_task(
    task_id: int,
    data: MyTaskUpdate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = TaskService(db)

    return await service.update_my_task(
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )