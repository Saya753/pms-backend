from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project, ProjectMember
from app.modules.tasks.models import Task


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # USER PROJECTS
    # =========================================================

    async def get_user_project_ids(
        self,
        user_id: int,
    ) -> list[int]:

        result = await self.db.execute(
            select(ProjectMember.project_id)
            .where(
                ProjectMember.user_id == user_id
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # PROJECTS
    # =========================================================

    async def get_projects_by_ids(
        self,
        project_ids: list[int],
    ) -> list[Project]:

        if not project_ids:
            return []

        result = await self.db.execute(
            select(Project)
            .where(
                Project.id.in_(project_ids)
            )
            .order_by(
                Project.created_at.desc()
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # USER TASKS
    # =========================================================

    async def get_user_tasks(
        self,
        user_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .where(
                Task.assignee_id == user_id
            )
            .order_by(
                Task.due_date.asc(),
                Task.created_at.desc(),
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # PROJECT TASKS
    # =========================================================

    async def get_tasks_by_project_ids(
        self,
        project_ids: list[int],
    ) -> list[Task]:

        if not project_ids:
            return []

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id.in_(project_ids)
            )
            .order_by(
                Task.created_at.desc()
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # TOP LEVEL PROJECT TASKS
    # =========================================================

    async def get_main_tasks_by_project_ids(
        self,
        project_ids: list[int],
    ) -> list[Task]:

        if not project_ids:
            return []

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id.in_(project_ids),
                Task.parent_id.is_(None),
            )
            .order_by(
                Task.created_at.desc()
            )
        )

        return list(result.scalars().all())