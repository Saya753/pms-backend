from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.modules.comments.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.modules.comments.services import CommentService
from app.modules.users.models import User


comment_router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/comments",
    tags=["Comments"],
)


@comment_router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    organization_id: int,
    project_id: int,
    task_id: int,
    data: CommentCreate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = CommentService(db)

    return await service.create_comment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        data=data,
    )


@comment_router.get(
    "",
    response_model=list[CommentResponse],
)
async def get_task_comments(
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
    service = CommentService(db)

    return await service.get_task_comments(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


@comment_router.patch(
    "/{comment_id}",
    response_model=CommentResponse,
)
async def update_comment(
    organization_id: int,
    project_id: int,
    task_id: int,
    comment_id: int,
    data: CommentUpdate,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = CommentService(db)

    return await service.update_comment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        comment_id=comment_id,
        current_user_id=current_user.id,
        data=data,
    )


@comment_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    organization_id: int,
    project_id: int,
    task_id: int,
    comment_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = CommentService(db)

    await service.delete_comment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        comment_id=comment_id,
        current_user_id=current_user.id,
    )

    return None