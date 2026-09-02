from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project


class ProjectRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        organization_id: int,
        name: str,
        description: str | None,
        status: str,
        priority: str,
        start_date,
        end_date,
        budget,
    ) -> Project:

        project = Project(
            organization_id=organization_id,
            name=name,
            description=description,
            status=status,
            priority=priority,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
        )

        self.db.add(project)

        await self.db.flush()
        await self.db.refresh(project)

        return project