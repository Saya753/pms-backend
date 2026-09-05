from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.notifications.models import Notification


class NotificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

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

        notification = Notification(
            user_id=user_id,
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            invitation_id=invitation_id,
            type=notification_type,
            title=title,
            message=message,
            is_read=False,
        )

        self.db.add(notification)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(notification)

        return notification

    async def get_user_notifications(
        self,
        user_id: int,
    ) -> list[Notification]:

        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_notification(
        self,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:

        result = await self.db.execute(
            select(Notification)
            .where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def mark_as_read(
        self,
        notification: Notification,
    ) -> Notification:

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_all_as_read(
        self,
        user_id: int,
    ) -> int:

        result = await self.db.execute(
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )

        notifications = list(result.scalars().all())

        now = datetime.now(timezone.utc)

        for notification in notifications:
            notification.is_read = True
            notification.read_at = now

        await self.db.commit()

        return len(notifications)

    async def get_unread_count(
        self,
        user_id: int,
    ) -> int:

        result = await self.db.execute(
            select(func.count(Notification.id))
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )

        return result.scalar_one()
    
    async def get_notification_by_invitation(
        self,
        invitation_id: int,
        user_id: int,
    ) -> Notification | None:

        result = await self.db.execute(
            select(Notification)
            .where(
                Notification.invitation_id == invitation_id,
                Notification.user_id == user_id,
            )
            .order_by(
                Notification.created_at.desc()
            )
        )

        return result.scalars().first()