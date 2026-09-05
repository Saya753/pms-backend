from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import OrganizationMember, Organization
from app.modules.projects.models import (
    Project,
    ProjectMember,
    ProjectRole,
)
from app.modules.tasks.models import Task
from app.modules.users.models import User


class ProjectRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # =====================================================
    # PROJECT
    # =====================================================

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

    async def get_organization_projects(
        self,
        organization_id: int,
        search: str | None = None,
        status_filter: str | None = None,
    ) -> list[Project]:

        query = (
            select(Project)
            .where(
                Project.organization_id == organization_id
            )
        )

        if search:
            query = query.where(
                Project.name.ilike(f"%{search}%")
            )

        if status_filter:
            query = query.where(
                Project.status == status_filter
            )

        query = query.order_by(
            Project.created_at.desc()
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def get_project(
        self,
        project_id: int,
        organization_id: int,
    ) -> Project | None:

        result = await self.db.execute(
            select(Project)
            .where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
        )

        return result.scalar_one_or_none()

    async def update_project(
        self,
        project: Project,
        name: str | None,
        description: str | None,
        budget: float | None,
        start_date,
        end_date,
        status: str | None,
        priority: str | None,
    ) -> Project:

        if name is not None:
            project.name = name

        if description is not None:
            project.description = description

        if budget is not None:
            project.budget = budget

        if start_date is not None:
            project.start_date = start_date

        if end_date is not None:
            project.end_date = end_date

        if status is not None:
            project.status = status

        if priority is not None:
            project.priority = priority

        await self.db.flush()

        await self.db.refresh(project)

        return project

    async def delete_project(
        self,
        project: Project,
    ) -> None:

        await self.db.delete(project)

        await self.db.flush()

    # =====================================================
    # PROJECT ROLE
    # =====================================================

    async def get_project_role_by_name(
        self,
        role_name: str,
    ) -> ProjectRole | None:

        result = await self.db.execute(
            select(ProjectRole)
            .where(
                ProjectRole.name == role_name
            )
        )

        return result.scalar_one_or_none()

    async def get_project_member_by_role(
        self,
        project_id: int,
        role_id: int,
    ) -> ProjectMember | None:

        result = await self.db.execute(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.project_role_id == role_id,
            )
        )

        return result.scalar_one_or_none()

    # =====================================================
    # PROJECT MEMBER
    # =====================================================

    async def get_project_member(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectMember | None:

        result = await self.db.execute(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def create_project_member(
        self,
        project_id: int,
        user_id: int,
        project_role_id: int,
    ) -> ProjectMember:

        project_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            project_role_id=project_role_id,
        )

        self.db.add(project_member)

        await self.db.flush()

        await self.db.refresh(project_member)

        return project_member

    async def get_project_members(
        self,
        project_id: int,
    ):

        result = await self.db.execute(
            select(
                ProjectMember,
                User.username,
                User.full_name,
            )
            .join(
                User,
                User.id == ProjectMember.user_id,
            )
            .where(
                ProjectMember.project_id == project_id
            )
        )

        rows = result.all()

        return [
            {
                "id": member.id,
                "project_id": member.project_id,
                "user_id": member.user_id,
                "username": username,
                "full_name": full_name,
                "project_role": member.project_role,
                "joined_at": member.joined_at,
            }
            for member, username, full_name in rows
        ]

    async def update_project_member_role(
        self,
        project_member: ProjectMember,
        role_id: int,
    ) -> ProjectMember:

        project_member.project_role_id = role_id

        await self.db.flush()

        await self.db.refresh(project_member)

        return project_member

    async def delete_project_member(
        self,
        project_member: ProjectMember,
    ) -> None:

        await self.db.delete(project_member)

        await self.db.flush()

    # =====================================================
    # MY PROJECTS
    # =====================================================

    async def get_user_projects(
        self,
        user_id: int,
        search: str | None = None,
        organization_id: int | None = None,
        status_filter: str | None = None,
    ) -> list[tuple[Project, ProjectRole]]:

        query = (
            select(Project, ProjectRole)
            .join(
                ProjectMember,
                ProjectMember.project_id == Project.id,
            )
            .join(
                ProjectRole,
                ProjectRole.id == ProjectMember.project_role_id,
            )
            .where(
                ProjectMember.user_id == user_id,
            )
        )

        if search:
            query = query.where(
                Project.name.ilike(f"%{search}%")
            )

        if organization_id is not None:
            query = query.where(
                Project.organization_id == organization_id
            )

        if status_filter:
            query = query.where(
                Project.status == status_filter
            )

        query = query.order_by(
            Project.created_at.desc()
        )

        result = await self.db.execute(query)

        return list(result.all())

    # =====================================================
    # SEARCH USERS IN ORGANIZATION
    # =====================================================

    async def search_organization_members(
        self,
        organization_id: int,
        search: str,
    ):

        result = await self.db.execute(
            select(
                User.id,
                User.username,
                User.full_name,
            )
            .join(
                OrganizationMember,
                OrganizationMember.user_id == User.id,
            )
            .where(
                OrganizationMember.organization_id == organization_id,
                User.username.ilike(f"%{search}%"),
            )
            .order_by(User.username)
            .limit(20)
        )

        return result.all()

    # =====================================================
    # PROJECTS VISIBLE TO ORGANIZATION MEMBER
    # =====================================================

    async def get_visible_projects(
        self,
        user_id: int,
        organization_id: int | None = None,
        search: str | None = None,
        status_filter: str | None = None,
    ):

        query = (
            select(Project, Organization.name)
            .join(
                Organization,
                Organization.id == Project.organization_id,
            )
            .join(
                OrganizationMember,
                OrganizationMember.organization_id
                == Project.organization_id,
            )
            .where(
                OrganizationMember.user_id == user_id,
            )
        )

        if organization_id is not None:
            query = query.where(
                Project.organization_id == organization_id
            )

        if search:
            query = query.where(
                Project.name.ilike(f"%{search}%")
            )

        if status_filter:
            query = query.where(
                Project.status == status_filter
            )

        query = query.order_by(
            Project.created_at.desc()
        )

        result = await self.db.execute(query)

        return list(result.all())

    # =====================================================
    # PROJECT PROGRESS
    # =====================================================

    async def get_project_progress(
        self,
        project_id: int,
    ) -> float:

        result = await self.db.execute(
            select(
                func.coalesce(
                    func.avg(Task.progress),
                    0,
                )
            )
            .where(
                Task.project_id == project_id,
                Task.parent_id.is_(None),
            )
        )

        progress = result.scalar_one()

        return round(float(progress), 2)