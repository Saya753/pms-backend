from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity_logs.models import ActivityLog


class ActivityLogRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        organization_id: int,
        project_id: int | None,
        task_id: int | None,
        user_id: int,
        action: str,
        description: str,
        old_value: str | None = None,
        new_value: str | None = None,
    ) -> ActivityLog:

        log = ActivityLog(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            user_id=user_id,
            action=action,
            description=description,
            old_value=old_value,
            new_value=new_value,
        )

        self.db.add(log)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(log)

        return log

    async def get_project_logs(
        self,
        project_id: int,
    ) -> list[ActivityLog]:

        result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.project_id == project_id,
            )
            .order_by(
                ActivityLog.created_at.desc(),
            )
        )

        return list(result.scalars().all())

    async def get_task_logs(
        self,
        task_id: int,
    ) -> list[ActivityLog]:

        result = await self.db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.task_id == task_id,
            )
            .order_by(
                ActivityLog.created_at.desc(),
            )
        )

        return list(result.scalars().all())