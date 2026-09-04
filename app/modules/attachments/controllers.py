from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.modules.attachments.schemas import AttachmentResponse
from app.modules.attachments.services import AttachmentService
from app.core.dependencies import get_current_user
from app.modules.users.models import User


attachment_router = APIRouter(
    prefix="/organizations/{organization_id}/projects/{project_id}/tasks/{task_id}/attachments",
    tags=["Attachments"],
)


@attachment_router.post(
    "",
    response_model=AttachmentResponse,
    status_code=201,
)
async def upload_attachment(
    organization_id: int,
    project_id: int,
    task_id: int,
    file: Annotated[UploadFile, File()],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = AttachmentService(db)

    return await service.upload_attachment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
        file=file,
    )


@attachment_router.get(
    "",
    response_model=list[AttachmentResponse],
)
async def get_task_attachments(
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
    service = AttachmentService(db)

    return await service.get_task_attachments(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        current_user_id=current_user.id,
    )


@attachment_router.get(
    "/{attachment_id}",
)
async def download_attachment(
    organization_id: int,
    project_id: int,
    task_id: int,
    attachment_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = AttachmentService(db)

    attachment = await service.get_attachment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        attachment_id=attachment_id,
        current_user_id=current_user.id,
    )

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.original_filename,
        media_type=attachment.content_type or "application/octet-stream",
    )


@attachment_router.delete(
    "/{attachment_id}",
    status_code=204,
)
async def delete_attachment(
    organization_id: int,
    project_id: int,
    task_id: int,
    attachment_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = AttachmentService(db)

    await service.delete_attachment(
        organization_id=organization_id,
        project_id=project_id,
        task_id=task_id,
        attachment_id=attachment_id,
        current_user_id=current_user.id,
    )

    return None