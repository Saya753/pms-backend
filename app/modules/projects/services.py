from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.repositories import ProjectRepository
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.organizations.repositories import OrganizationRepository
from app.modules.projects.models import Project


class ProjectService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ProjectRepository(db)
        self.organization_repository = OrganizationRepository(db)

    async def create_project(
        self,
        organization_id: int,
        current_user_id: int,
        data: ProjectCreate,
    ):

        # بررسی اینکه کاربر اجازه ساخت پروژه دارد
        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.create",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create projects",
            )

        project = await self.repository.create(
            organization_id=organization_id,
            name=data.name,
            description=data.description,
            status=data.status,
            priority=data.priority,
            start_date=data.start_date,
            end_date=data.end_date,
            budget=data.budget,
        )

        await self.db.commit()
        await self.db.refresh(project)

        return project
    
    async def get_organization_projects(
        self,
        organization_id: int,
        current_user_id: int,
    ) -> list[Project]:

        # بررسی Permission
        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.read",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view projects",
            )

        return await self.repository.get_organization_projects(
            organization_id=organization_id,
        )
        
    async def update_project(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        data: ProjectUpdate,
    ) -> Project:

        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.update",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update projects",
            )

        project = await self.repository.get_project(
            project_id=project_id,
            organization_id=organization_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        updated_project = await self.repository.update_project(
            project=project,
            name=data.name,
            description=data.description,
            budget=data.budget,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
        )

        await self.db.commit()
        await self.db.refresh(updated_project)

        return updated_project
    
    async def delete_project(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ) -> None:

        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.delete",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete projects",
            )

        project = await self.repository.get_project(
            project_id=project_id,
            organization_id=organization_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await self.repository.delete_project(project)

        await self.db.commit()