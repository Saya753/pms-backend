import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.repositories import AttachmentRepository
from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.repositories import TaskRepository
from app.modules.activity_logs.repositories import ActivityLogRepository


UPLOAD_DIR = Path("uploads")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".zip",
}


class AttachmentService:

    def __init__(self, db: AsyncSession):
        self.db = db

        self.repository = AttachmentRepository(db)
        self.task_repository = TaskRepository(db)
        self.project_repository = ProjectRepository(db)
        self.activity_repository = ActivityLogRepository(db)

    async def _get_task_or_404(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
    ):

        project = await self.project_repository.get_project(
            project_id=project_id,
            organization_id=organization_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        task = await self.task_repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    async def _get_project_member(
        self,
        project_id: int,
        user_id: int,
    ):

        member = await self.project_repository.get_project_member(
            project_id=project_id,
            user_id=user_id,
        )

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project",
            )

        return member

    async def upload_attachment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        file: UploadFile,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required",
            )

        original_filename = Path(file.filename).name

        extension = Path(original_filename).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "File type is not allowed. "
                    f"Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                ),
            )

        file_content = await file.read()

        file_size = len(file_content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size cannot exceed 10 MB",
            )

        stored_filename = f"{uuid.uuid4()}{extension}"

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = UPLOAD_DIR / stored_filename

        # Save physical file
        try:
            with open(file_path, "wb") as destination:
                destination.write(file_content)

        except Exception:
            if file_path.exists():
                file_path.unlink()

            raise

        # Create database record
        try:
            attachment = await self.repository.create_attachment(
                task_id=task_id,
                uploaded_by=current_user_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                content_type=file.content_type,
                file_size=file_size,
            )

        except Exception:
            # DB record creation failed, so remove physical file
            if file_path.exists():
                file_path.unlink()

            raise

        # Activity Log
        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            user_id=current_user_id,
            action="ATTACHMENT_UPLOADED",
            description=(
                f'Attachment "{attachment.original_filename}" was uploaded'
            ),
        )

        return attachment

    async def get_task_attachments(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        return await self.repository.get_task_attachments(
            task_id=task_id,
        )

    async def get_attachment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        attachment_id: int,
        current_user_id: int,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        attachment = await self.repository.get_attachment(
            attachment_id=attachment_id,
            task_id=task_id,
        )

        if attachment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found",
            )

        file_path = Path(attachment.file_path)

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment file not found on server",
            )

        return attachment

    async def delete_attachment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        attachment_id: int,
        current_user_id: int,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        member = await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        attachment = await self.repository.get_attachment(
            attachment_id=attachment_id,
            task_id=task_id,
        )

        if attachment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found",
            )

        role_name = member.project_role.name

        if (
            attachment.uploaded_by != current_user_id
            and role_name not in {"PROJECT_MANAGER", "TEAM_LEAD"}
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own attachments",
            )

        file_path = Path(attachment.file_path)

        await self.repository.delete_attachment(
            attachment=attachment,
        )

        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass