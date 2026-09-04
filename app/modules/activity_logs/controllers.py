from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.activity_logs.schemas import ActivityLogResponse
from app.modules.activity_logs.services import ActivityLogService
from app.core.dependencies import get_current_user

from app.modules.users.models import User


activity_log_router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}",
    tags=["Activity Logs"],
)


@activity_log_router.get(
    "/activity-logs",
    response_model=list[ActivityLogResponse],
)
async def get_project_activity_logs(
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

    service = ActivityLogService(db)

    return await service.get_project_logs(
        organization_id=organization_id,
        project_id=project_id,
        current_user_id=current_user.id,
    )


@activity_log_router.get(
    "/tasks/{task_id}/activity-logs",
    response_model=list[ActivityLogResponse],
)
async def get_task_activity_logs(
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

    service = ActivityLogService(db)

    return await service.get_task_logs(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )