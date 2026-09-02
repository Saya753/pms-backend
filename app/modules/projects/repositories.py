from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import (
    Project,
    ProjectMember,
    ProjectRole,
)


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
    
    async def get_organization_projects(
        self,
        organization_id: int,
    ) -> list[Project]:

        result = await self.db.execute(
            select(Project)
            .where(Project.organization_id == organization_id)
            .order_by(Project.created_at.desc())
        )

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

        await self.db.flush()
        await self.db.refresh(project)

        return project
    
    async def delete_project(
        self,
        project: Project,
    ) -> None:
        await self.db.delete(project)
        await self.db.flush()
        
    async def get_project_role_by_name(
        self,
        role_name: str,
    ) -> ProjectRole | None:

        result = await self.db.execute(
            select(ProjectRole).where(
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
    ) -> list[ProjectMember]:

        result = await self.db.execute(
            select(ProjectMember)
            .where(
                ProjectMember.project_id == project_id
            )
            .order_by(ProjectMember.joined_at.asc())
        )

        return list(result.scalars().all())
    
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