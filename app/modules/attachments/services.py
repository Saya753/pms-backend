import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import Attachment
from app.modules.attachments.repositories import AttachmentRepository
from app.modules.activity_logs.repositories import ActivityLogRepository
from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.repositories import TaskRepository


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

    # =========================================================
    # Common Helpers
    # =========================================================

    async def _validate_file(
        self,
        file: UploadFile,
    ) -> tuple[str, str, bytes, int]:

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
                    f"Allowed extensions: "
                    f"{', '.join(sorted(ALLOWED_EXTENSIONS))}"
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

        return (
            original_filename,
            extension,
            file_content,
            file_size,
        )

    async def _save_file(
        self,
        *,
        file_content: bytes,
        extension: str,
    ) -> tuple[str, str, Path]:

        stored_filename = f"{uuid.uuid4()}{extension}"

        UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = UPLOAD_DIR / stored_filename

        try:
            with open(file_path, "wb") as destination:
                destination.write(file_content)

        except Exception:
            if file_path.exists():
                file_path.unlink()

            raise

        return (
            stored_filename,
            str(file_path),
            file_path,
        )

    # =========================================================
    # Task Helpers
    # =========================================================

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

    # =========================================================
    # Task Attachment - Upload
    # =========================================================

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

        (
            original_filename,
            extension,
            file_content,
            file_size,
        ) = await self._validate_file(file)

        (
            stored_filename,
            file_path,
            physical_path,
        ) = await self._save_file(
            file_content=file_content,
            extension=extension,
        )

        try:
            attachment = await self.repository.create_attachment(
                task_id=task_id,
                project_id=None,
                uploaded_by=current_user_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                content_type=file.content_type,
                file_size=file_size,
            )

        except Exception:
            if physical_path.exists():
                physical_path.unlink()

            raise

        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            user_id=current_user_id,
            action="ATTACHMENT_UPLOADED",
            description=(
                f'Attachment "{attachment.original_filename}" '
                f'was uploaded'
            ),
        )

        return attachment

    # =========================================================
    # Task Attachment - List
    # =========================================================

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

    # =========================================================
    # Task Attachment - Download
    # =========================================================

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

    # =========================================================
    # Task Attachment - Delete
    # =========================================================

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
            and role_name not in {
                "PROJECT_MANAGER",
                "TEAM_LEAD",
            }
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

    # =========================================================
    # Project Helpers
    # =========================================================

    async def _get_project_or_404(
        self,
        organization_id: int,
        project_id: int,
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

        return project

    async def _validate_project_access(
        self,
        project_id: int,
        current_user_id: int,
    ):

        member = await self.project_repository.get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project",
            )

        return member

    # =========================================================
    # Project Attachment - Upload
    # =========================================================

    async def upload_project_attachment(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        file: UploadFile,
    ):

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._validate_project_access(
            project_id=project_id,
            current_user_id=current_user_id,
        )

        (
            original_filename,
            extension,
            file_content,
            file_size,
        ) = await self._validate_file(file)

        (
            stored_filename,
            file_path,
            physical_path,
        ) = await self._save_file(
            file_content=file_content,
            extension=extension,
        )

        try:
            attachment = await self.repository.create_attachment(
                task_id=None,
                project_id=project_id,
                uploaded_by=current_user_id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=file_path,
                content_type=file.content_type,
                file_size=file_size,
            )

        except Exception:
            if physical_path.exists():
                physical_path.unlink()

            raise

        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=None,
            user_id=current_user_id,
            action="ATTACHMENT_UPLOADED",
            description=(
                f'Project attachment '
                f'"{attachment.original_filename}" was uploaded'
            ),
        )

        return attachment

    # =========================================================
    # Project Attachment - List
    # =========================================================

    async def get_project_attachments(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ):

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._validate_project_access(
            project_id=project_id,
            current_user_id=current_user_id,
        )

        return await self.repository.get_project_attachments(
            project_id=project_id,
        )

    # =========================================================
    # Project Attachment - Download
    # =========================================================

    async def get_project_attachment(
        self,
        organization_id: int,
        project_id: int,
        attachment_id: int,
        current_user_id: int,
    ):

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._validate_project_access(
            project_id=project_id,
            current_user_id=current_user_id,
        )

        attachment = await self.repository.get_project_attachment(
            attachment_id=attachment_id,
            project_id=project_id,
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

    # =========================================================
    # Project Attachment - Delete
    # =========================================================

    async def delete_project_attachment(
        self,
        organization_id: int,
        project_id: int,
        attachment_id: int,
        current_user_id: int,
    ):

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        member = await self._validate_project_access(
            project_id=project_id,
            current_user_id=current_user_id,
        )

        attachment = await self.repository.get_project_attachment(
            attachment_id=attachment_id,
            project_id=project_id,
        )

        if attachment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attachment not found",
            )

        role_name = member.project_role.name

        if (
            attachment.uploaded_by != current_user_id
            and role_name not in {
                "PROJECT_MANAGER",
                "TEAM_LEAD",
            }
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