from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.repositories import ProjectRepository
from app.modules.projects.schemas import ProjectCreate
from app.modules.organizations.repositories import OrganizationRepository

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