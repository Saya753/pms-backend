from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reports.repositories import ReportsRepository
from app.modules.reports.schemas import (
    PerformanceSummary,
    ProjectReportItem,
    ReportSummary,
    ReportsResponse,
)


class ReportsService:

    COMPLETED_PROJECT_STATUSES = {
        "DONE",
        "COMPLETED",
        "CANCELLED",
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = ReportsRepository(db)

    # --------------------------------------------------
    # Calculations
    # --------------------------------------------------

    def _calculate_project_progress(
        self,
        project_id: int,
        tasks,
    ) -> float:

        main_tasks = [
            task
            for task in tasks
            if task.project_id == project_id
            and task.parent_id is None
        ]

        if not main_tasks:
            return 0.0

        progress = (
            sum(task.progress for task in main_tasks)
            / len(main_tasks)
        )

        return round(progress, 2)

    def _is_project_delayed(
        self,
        project,
        today: date,
    ) -> bool:

        if project.end_date is None:
            return False

        if project.end_date >= today:
            return False

        return project.status not in self.COMPLETED_PROJECT_STATUSES

    # --------------------------------------------------
    # Build report
    # --------------------------------------------------

    async def _build_report(
        self,
        projects,
    ) -> ReportsResponse:

        project_ids = [
            project.id
            for project in projects
        ]

        tasks = await self.repository.get_tasks_by_project_ids(
            project_ids=project_ids
        )

        today = date.today()

        project_reports = []

        total_completed_tasks = 0
        project_progress_values = []

        for project in projects:

            project_tasks = [
                task
                for task in tasks
                if task.project_id == project.id
            ]

            total_tasks = len(project_tasks)

            completed_tasks = sum(
                1
                for task in project_tasks
                if task.status == "DONE"
            )

            total_completed_tasks += completed_tasks

            completion_rate = (
                (completed_tasks / total_tasks) * 100
                if total_tasks > 0
                else 0.0
            )

            progress = self._calculate_project_progress(
                project.id,
                tasks,
            )

            project_progress_values.append(progress)

            is_delayed = self._is_project_delayed(
                project,
                today,
            )

            project_reports.append(
                ProjectReportItem(
                    project_id=project.id,
                    project_name=project.name,
                    status=project.status,
                    progress=progress,
                    total_tasks=total_tasks,
                    completed_tasks=completed_tasks,
                    task_completion_rate=round(
                        completion_rate,
                        2,
                    ),
                    due_date=project.end_date,
                    is_delayed=is_delayed,
                )
            )

        total_tasks = len(tasks)

        task_completion_rate = (
            (total_completed_tasks / total_tasks) * 100
            if total_tasks > 0
            else 0.0
        )

        average_project_progress = (
            sum(project_progress_values)
            / len(project_progress_values)
            if project_progress_values
            else 0.0
        )

        return ReportsResponse(
            summary=ReportSummary(
                total_projects=len(projects),
                total_tasks=total_tasks,
                completed_tasks=total_completed_tasks,
                average_project_progress=round(
                    average_project_progress,
                    2,
                ),
            ),
            projects=project_reports,
            performance=PerformanceSummary(
                task_completion_rate=round(
                    task_completion_rate,
                    2,
                ),
                average_project_progress=round(
                    average_project_progress,
                    2,
                ),
            ),
        )

    # --------------------------------------------------
    # General organization report
    # --------------------------------------------------

    async def get_general_report(
        self,
        current_user_id: int,
    ) -> ReportsResponse:

        roles = await self.repository.get_user_organization_roles(
            user_id=current_user_id
        )

        if "OWNER" not in roles and "ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only OWNER and ADMIN can view the general report"
                ),
            )

        projects = await self.repository.get_visible_projects(
            user_id=current_user_id
        )

        return await self._build_report(
            projects=projects
        )

    # --------------------------------------------------
    # Project report
    # --------------------------------------------------

    async def get_project_report(
        self,
        current_user_id: int,
        project_id: int,
    ) -> ReportsResponse:

        project = await self.repository.get_project_by_id(
            project_id=project_id
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Check organization role
        organization_role = (
            await self.repository.get_user_organization_role(
                user_id=current_user_id,
                organization_id=project.organization_id,
            )
        )

        # OWNER / ADMIN can access the project report
        if organization_role in {"OWNER", "ADMIN"}:
            return await self._build_report(
                projects=[project]
            )

        # PROJECT_MANAGER can access only their own project
        is_manager = await self.repository.is_project_manager(
            user_id=current_user_id,
            project_id=project_id,
        )

        if is_manager:
            return await self._build_report(
                projects=[project]
            )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to view this project report"
            ),
        )

    # --------------------------------------------------
    # General Excel export
    # --------------------------------------------------

    async def get_general_export_projects(
        self,
        current_user_id: int,
    ):

        roles = await self.repository.get_user_organization_roles(
            user_id=current_user_id
        )

        if "OWNER" not in roles and "ADMIN" not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only OWNER and ADMIN can export "
                    "the general report"
                ),
            )

        return await self.repository.get_visible_projects(
            user_id=current_user_id
        )

    # --------------------------------------------------
    # Project Excel export
    # --------------------------------------------------

    async def get_project_export(
        self,
        current_user_id: int,
        project_id: int,
    ):

        project = await self.repository.get_project_by_id(
            project_id=project_id
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        organization_role = (
            await self.repository.get_user_organization_role(
                user_id=current_user_id,
                organization_id=project.organization_id,
            )
        )

        # OWNER / ADMIN
        if organization_role in {"OWNER", "ADMIN"}:
            return project

        # PROJECT_MANAGER of THIS project
        is_manager = await self.repository.is_project_manager(
            user_id=current_user_id,
            project_id=project_id,
        )

        if is_manager:
            return project

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only OWNER, ADMIN or "
                "the PROJECT_MANAGER of this project "
                "can export the project report"
            ),
        )