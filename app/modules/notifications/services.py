from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification
from app.modules.notifications.repositories import NotificationRepository


class NotificationService:

    def __init__(self, db: AsyncSession):
        self.repository = NotificationRepository(db)

    async def create_notification(
        self,
        user_id: int,
        organization_id: int | None,
        project_id: int | None,
        task_id: int | None,
        invitation_id: int | None,
        notification_type: str,
        title: str,
        message: str,
    ) -> Notification:

        return await self.repository.create_notification(
            user_id=user_id,
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            invitation_id=invitation_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )

    async def get_my_notifications(
        self,
        current_user_id: int,
    ) -> list[Notification]:

        return await self.repository.get_user_notifications(
            user_id=current_user_id,
        )

    async def mark_as_read(
        self,
        notification_id: int,
        current_user_id: int,
    ) -> Notification:

        notification = await self.repository.get_notification(
            notification_id=notification_id,
            user_id=current_user_id,
        )

        if notification is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )

        return await self.repository.mark_as_read(
            notification=notification,
        )

    async def mark_all_as_read(
        self,
        current_user_id: int,
    ) -> int:

        return await self.repository.mark_all_as_read(
            user_id=current_user_id,
        )

    async def get_unread_count(
        self,
        current_user_id: int,
    ) -> int:

        return await self.repository.get_unread_count(
            user_id=current_user_id,
        )