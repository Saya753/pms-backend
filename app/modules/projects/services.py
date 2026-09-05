from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.repositories import OrganizationRepository
from app.modules.projects.models import ProjectMember
from app.modules.projects.repositories import ProjectRepository
from app.modules.projects.schemas import (
    MyProjectResponse,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectFilterResponse,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberResponse,
    ProjectMemberRoleUpdate,
    ProjectMemberSearchResponse,
    ProjectResponse,
    ProjectRoleResponse,
    ProjectUpdate,
)


class ProjectService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ProjectRepository(db)
        self.organization_repository = OrganizationRepository(db)

    # =====================================================
    # VALIDATION
    # =====================================================

    @staticmethod
    def validate_project_data(
        start_date,
        end_date,
        status_value: str | None = None,
        priority: str | None = None,
    ):

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be before start date",
            )

        allowed_statuses = {
            "PLANNING",
            "IN_PROGRESS",
            "COMPLETED",
            "CANCELLED",
        }

        allowed_priorities = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "URGENT",
        }

        if (
            status_value is not None
            and status_value not in allowed_statuses
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project status",
            )

        if (
            priority is not None
            and priority not in allowed_priorities
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project priority",
            )

    # =====================================================
    # CREATE PROJECT
    # =====================================================

    async def create_project(
        self,
        organization_id: int,
        current_user_id: int,
        data: ProjectCreate,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.create",
            )
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create projects",
            )

        organization = (
            await self.organization_repository.get_organization(
                organization_id=organization_id
            )
        )

        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        self.validate_project_data(
            start_date=data.start_date,
            end_date=data.end_date,
            status_value=data.status,
            priority=data.priority,
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

    # =====================================================
    # GET ORGANIZATION PROJECTS
    # =====================================================

    async def get_organization_projects(
        self,
        organization_id: int,
        current_user_id: int,
        search: str | None = None,
        status_filter: str | None = None,
    ) -> list[ProjectListResponse]:

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.read",
            )
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view projects",
            )

        organization = (
            await self.organization_repository.get_organization(
                organization_id=organization_id
            )
        )

        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        projects = await self.repository.get_organization_projects(
            organization_id=organization_id,
            search=search,
            status_filter=status_filter,
        )

        result = []

        for project in projects:

            progress = await self.repository.get_project_progress(
                project.id
            )

            result.append(
                ProjectListResponse(
                    id=project.id,
                    organization_id=project.organization_id,
                    organization_name=organization.name,
                    name=project.name,
                    description=project.description,
                    status=project.status,
                    priority=project.priority,
                    start_date=project.start_date,
                    end_date=project.end_date,
                    budget=(
                        float(project.budget)
                        if project.budget is not None
                        else None
                    ),
                    progress=progress,
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )
            )

        return result

    # =====================================================
    # PROJECT DETAIL
    # =====================================================

    async def get_project_detail(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ):

        organization_member = (
            await self.organization_repository.get_member(
                organization_id=organization_id,
                user_id=current_user_id,
            )
        )

        if organization_member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
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

        organization = (
            await self.organization_repository.get_organization(
                organization_id=organization_id
            )
        )

        progress = await self.repository.get_project_progress(
            project_id=project.id
        )

        members = await self.repository.get_project_members(
            project_id=project.id
        )

        return ProjectDetailResponse(
            id=project.id,
            organization_id=project.organization_id,
            organization_name=organization.name,
            name=project.name,
            description=project.description,
            status=project.status,
            priority=project.priority,
            start_date=project.start_date,
            end_date=project.end_date,
            budget=(
                float(project.budget)
                if project.budget is not None
                else None
            ),
            progress=progress,
            members=members,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    # =====================================================
    # UPDATE PROJECT
    # =====================================================

    async def update_project(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        data: ProjectUpdate,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.update",
            )
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

        final_start_date = (
            data.start_date
            if data.start_date is not None
            else project.start_date
        )

        final_end_date = (
            data.end_date
            if data.end_date is not None
            else project.end_date
        )

        self.validate_project_data(
            start_date=final_start_date,
            end_date=final_end_date,
            status_value=data.status,
            priority=data.priority,
        )

        updated_project = await self.repository.update_project(
            project=project,
            name=data.name,
            description=data.description,
            budget=data.budget,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
            priority=data.priority,
        )

        await self.db.commit()

        await self.db.refresh(updated_project)

        return updated_project

    # =====================================================
    # DELETE PROJECT
    # =====================================================

    async def delete_project(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.delete",
            )
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

    # =====================================================
    # ADD PROJECT MEMBER
    # =====================================================

    async def add_project_member(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        data: ProjectMemberCreate,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.update",
            )
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

        organization_member = (
            await self.organization_repository.get_member(
                organization_id=organization_id,
                user_id=data.user_id,
            )
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

        role_name = data.role.upper()

        project_role = (
            await self.repository.get_project_role_by_name(
                role_name
            )
        )

        if project_role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project role",
            )

        if role_name in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:

            existing_role_member = (
                await self.repository.get_project_member_by_role(
                    project_id=project_id,
                    role_id=project_role.id,
                )
            )

            if existing_role_member is not None:

                if role_name == "PROJECT_MANAGER":
                    detail = (
                        "This project already has a Project Manager"
                    )
                else:
                    detail = (
                        "This project already has a Team Lead"
                    )

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail,
                )

        project_member = (
            await self.repository.create_project_member(
                project_id=project_id,
                user_id=data.user_id,
                project_role_id=project_role.id,
            )
        )

        await self.db.commit()

        await self.db.refresh(project_member)

        return project_member

    # =====================================================
    # UPDATE MEMBER ROLE
    # =====================================================

    async def update_project_member_role(
        self,
        organization_id: int,
        project_id: int,
        target_user_id: int,
        current_user_id: int,
        data: ProjectMemberRoleUpdate,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.update",
            )
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

        role_name = data.role.upper()

        project_role = (
            await self.repository.get_project_role_by_name(
                role_name
            )
        )

        if project_role is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project role",
            )

        if role_name in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:

            existing_role_member = (
                await self.repository.get_project_member_by_role(
                    project_id=project_id,
                    role_id=project_role.id,
                )
            )

            if (
                existing_role_member is not None
                and existing_role_member.id != project_member.id
            ):

                if role_name == "PROJECT_MANAGER":
                    detail = (
                        "This project already has a Project Manager"
                    )
                else:
                    detail = (
                        "This project already has a Team Lead"
                    )

                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=detail,
                )

        updated_member = (
            await self.repository.update_project_member_role(
                project_member=project_member,
                role_id=project_role.id,
            )
        )

        await self.db.commit()

        await self.db.refresh(updated_member)

        return updated_member

    # =====================================================
    # REMOVE MEMBER
    # =====================================================

    async def remove_project_member(
        self,
        organization_id: int,
        project_id: int,
        target_user_id: int,
        current_user_id: int,
    ):

        has_permission = (
            await self.organization_repository.member_has_permission(
                organization_id=organization_id,
                user_id=current_user_id,
                permission_name="project.update",
            )
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

        await self.repository.delete_project_member(
            project_member
        )

        await self.db.commit()

    # =====================================================
    # GET PROJECT MEMBERS
    # =====================================================

    async def get_project_members(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ):

        organization_member = (
            await self.organization_repository.get_member(
                organization_id=organization_id,
                user_id=current_user_id,
            )
        )

        if organization_member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
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

        return await self.repository.get_project_members(
            project_id=project_id,
        )

    # =====================================================
    # MY PROJECTS
    # =====================================================

    async def get_user_projects(
        self,
        user_id: int,
        search: str | None = None,
        organization_id: int | None = None,
        status_filter: str | None = None,
    ):

        projects = await self.repository.get_user_projects(
            user_id=user_id,
            search=search,
            organization_id=organization_id,
            status_filter=status_filter,
        )

        return [
            MyProjectResponse(
                id=project.id,
                organization_id=project.organization_id,
                name=project.name,
                description=project.description,
                status=project.status,
                priority=project.priority,
                start_date=project.start_date,
                end_date=project.end_date,
                budget=(
                    float(project.budget)
                    if project.budget is not None
                    else None
                ),
                role=ProjectRoleResponse(
                    id=role.id,
                    name=role.name,
                ),
            )
            for project, role in projects
        ]

    # =====================================================
    # SEARCH MEMBERS
    # =====================================================

    async def search_organization_members(
        self,
        organization_id: int,
        current_user_id: int,
        search: str,
    ):

        current_member = (
            await self.organization_repository.get_member(
                organization_id=organization_id,
                user_id=current_user_id,
            )
        )

        if current_member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
            )

        if not search or len(search.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search must contain at least 2 characters",
            )

        users = await self.repository.search_organization_members(
            organization_id=organization_id,
            search=search.strip(),
        )

        return [
            ProjectMemberSearchResponse(
                user_id=user_id,
                username=username,
                full_name=full_name,
                organization_id=organization_id,
            )
            for user_id, username, full_name in users
        ]

    # =====================================================
    # VISIBLE PROJECTS
    # =====================================================

    async def get_visible_projects(
        self,
        current_user_id: int,
        organization_id: int | None = None,
        search: str | None = None,
        status_filter: str | None = None,
    ):

        if status_filter:
            self.validate_project_data(
                start_date=None,
                end_date=None,
                status_value=status_filter,
            )

        projects = await self.repository.get_visible_projects(
            user_id=current_user_id,
            organization_id=organization_id,
            search=search,
            status_filter=status_filter,
        )

        result = []

        for project, organization_name in projects:

            progress = await self.repository.get_project_progress(
                project.id
            )

            result.append(
                ProjectFilterResponse(
                    id=project.id,
                    name=project.name,
                    organization_id=project.organization_id,
                    organization_name=organization_name,
                    status=project.status,
                    priority=project.priority,
                    progress=progress,
                )
            )

        return result