from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import Attachment


class AttachmentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_attachment(
        self,
        task_id: int,
        uploaded_by: int,
        original_filename: str,
        stored_filename: str,
        file_path: str,
        content_type: str | None,
        file_size: int,
    ) -> Attachment:

        attachment = Attachment(
            task_id=task_id,
            uploaded_by=uploaded_by,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            content_type=content_type,
            file_size=file_size,
        )

        self.db.add(attachment)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(attachment)

        return attachment

    async def get_attachment(
        self,
        attachment_id: int,
        task_id: int,
    ) -> Attachment | None:

        result = await self.db.execute(
            select(Attachment).where(
                Attachment.id == attachment_id,
                Attachment.task_id == task_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_task_attachments(
        self,
        task_id: int,
    ) -> list[Attachment]:

        result = await self.db.execute(
            select(Attachment)
            .where(
                Attachment.task_id == task_id,
            )
            .order_by(
                Attachment.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    async def delete_attachment(
        self,
        attachment: Attachment,
    ) -> None:

        await self.db.delete(attachment)

        await self.db.flush()
        await self.db.commit()