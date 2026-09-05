from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import OrganizationMember, Role
from app.modules.projects.models import Project, ProjectMember
from app.modules.tasks.models import Task


class ReportsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------
    # Organization
    # -----------------------------

    async def get_user_organization_ids(self, user_id: int) -> list[int]:
        result = await self.db.execute(
            select(OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id == user_id
            )
        )

        return list(result.scalars().all())

    async def get_user_organization_roles(
        self,
        user_id: int,
    ) -> list[str]:

        result = await self.db.execute(
            select(Role.name)
            .join(
                OrganizationMember,
                OrganizationMember.role_id == Role.id,
            )
            .where(
                OrganizationMember.user_id == user_id
            )
        )

        return list(result.scalars().all())

    async def get_user_organization_role(
        self,
        user_id: int,
        organization_id: int,
    ) -> str | None:

        result = await self.db.execute(
            select(Role.name)
            .join(
                OrganizationMember,
                OrganizationMember.role_id == Role.id,
            )
            .where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )

        return result.scalar_one_or_none()

    # -----------------------------
    # Projects
    # -----------------------------

    async def get_visible_projects(
        self,
        user_id: int,
    ) -> list[Project]:

        organization_ids = await self.get_user_organization_ids(
            user_id=user_id
        )

        if not organization_ids:
            return []

        result = await self.db.execute(
            select(Project)
            .where(
                Project.organization_id.in_(organization_ids)
            )
            .order_by(
                Project.created_at.desc()
            )
        )

        return list(result.scalars().all())

    async def get_project_by_id(
        self,
        project_id: int,
    ) -> Project | None:

        result = await self.db.execute(
            select(Project)
            .where(
                Project.id == project_id
            )
        )

        return result.scalar_one_or_none()

    # -----------------------------
    # Project Manager
    # -----------------------------

    async def get_project_manager_projects(
        self,
        user_id: int,
    ) -> list[Project]:

        result = await self.db.execute(
            select(Project)
            .join(
                ProjectMember,
                ProjectMember.project_id == Project.id,
            )
            .join(
                Role,
                Role.id == ProjectMember.project_role_id,
            )
            .where(
                ProjectMember.user_id == user_id,
                Role.name == "PROJECT_MANAGER",
            )
            .order_by(
                Project.created_at.desc()
            )
        )

        return list(
            result.scalars().unique().all()
        )

    async def is_project_manager(
        self,
        user_id: int,
        project_id: int,
    ) -> bool:

        result = await self.db.execute(
            select(ProjectMember.id)
            .join(
                Role,
                Role.id == ProjectMember.project_role_id,
            )
            .where(
                ProjectMember.user_id == user_id,
                ProjectMember.project_id == project_id,
                Role.name == "PROJECT_MANAGER",
            )
        )

        return result.scalar_one_or_none() is not None

    # -----------------------------
    # Tasks
    # -----------------------------

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
                Task.project_id.asc(),
                Task.created_at.desc(),
            )
        )

        return list(result.scalars().all())