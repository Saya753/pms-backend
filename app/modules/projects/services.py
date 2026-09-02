from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.repositories import ProjectRepository
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
)
from app.modules.organizations.repositories import OrganizationRepository
from app.modules.projects.models import Project, ProjectMember


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
        
    async def add_project_member(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        data: ProjectMemberCreate,
    ) -> ProjectMember:

        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.update",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage project members",
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

        organization_member = await self.organization_repository.get_member(
            organization_id=organization_id,
            user_id=data.user_id,
        )

        if organization_member is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not a member of this organization",
            )

        existing_member = await self.repository.get_project_member(
            project_id=project_id,
            user_id=data.user_id,
        )

        if existing_member is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this project",
            )

        project_role = await self.repository.get_project_role_by_name(
            data.role
        )

        if project_role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project role",
            )
            
        # PROJECT_MANAGER and TEAM_LEAD can only have one member
        if data.role in {"PROJECT_MANAGER", "TEAM_LEAD"}:

            existing_role_member = await self.repository.get_project_member_by_role(
                project_id=project_id,
                role_id=project_role.id,
            )

            if existing_role_member is not None:

                if data.role == "PROJECT_MANAGER":
                    detail = "This project already has a Project Manager"
                else:
                    detail = "This project already has a Team Lead"

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail,
                )

        project_member = await self.repository.create_project_member(
            project_id=project_id,
            user_id=data.user_id,
            project_role_id=project_role.id,
        )

        await self.db.commit()
        await self.db.refresh(project_member)

        return project_member
    
    async def update_project_member_role(
        self,
        organization_id: int,
        project_id: int,
        target_user_id: int,
        current_user_id: int,
        data: ProjectMemberRoleUpdate,
    ) -> ProjectMember:

        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.update",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage project members",
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

        project_member = await self.repository.get_project_member(
            project_id=project_id,
            user_id=target_user_id,
        )

        if project_member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this project",
            )

        project_role = await self.repository.get_project_role_by_name(
            data.role
        )

        if project_role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project role",
            )

        # Only one Project Manager / Team Lead
        if data.role in {"PROJECT_MANAGER", "TEAM_LEAD"}:

            existing_role_member = await self.repository.get_project_member_by_role(
                project_id=project_id,
                role_id=project_role.id,
            )

            if (
                existing_role_member is not None
                and existing_role_member.id != project_member.id
            ):

                if data.role == "PROJECT_MANAGER":
                    detail = "This project already has a Project Manager"
                else:
                    detail = "This project already has a Team Lead"

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail,
                )

        updated_member = await self.repository.update_project_member_role(
            project_member=project_member,
            role_id=project_role.id,
        )

        await self.db.commit()
        await self.db.refresh(updated_member)

        return updated_member
    
    async def remove_project_member(
        self,
        organization_id: int,
        project_id: int,
        target_user_id: int,
        current_user_id: int,
    ) -> None:

        has_permission = await self.organization_repository.member_has_permission(
            organization_id=organization_id,
            user_id=current_user_id,
            permission_name="project.update",
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to manage project members",
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

        project_member = await self.repository.get_project_member(
            project_id=project_id,
            user_id=target_user_id,
        )

        if project_member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of this project",
            )

        await self.repository.delete_project_member(project_member)

        await self.db.commit()