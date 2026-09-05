from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.repositories import DashboardRepository
from app.modules.dashboard.schemas import (
    DashboardResponse,
    DashboardSummary,
    ProjectProgressItem,
    ProjectSummaryItem,
    TaskStatusDistribution,
)


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = DashboardRepository(db)

    async def get_dashboard(
        self,
        current_user_id: int,
    ) -> DashboardResponse:

        # =====================================================
        # 1. PROJECTS USER CAN SEE
        # =====================================================

        project_ids = await self.repository.get_user_project_ids(
            user_id=current_user_id
        )

        projects = await self.repository.get_projects_by_ids(
            project_ids=project_ids
        )

        # =====================================================
        # 2. ALL TASKS OF VISIBLE PROJECTS
        # =====================================================

        project_tasks = await self.repository.get_tasks_by_project_ids(
            project_ids=project_ids
        )

        # =====================================================
        # 3. USER'S OWN TASKS
        # =====================================================

        my_tasks = await self.repository.get_user_tasks(
            user_id=current_user_id
        )

        # =====================================================
        # 4. MY COMPLETED TASKS
        # =====================================================

        my_completed_tasks = [
            task
            for task in my_tasks
            if task.status == "DONE"
        ]

        # =====================================================
        # 5. MY DELAYED PROJECTS
        # =====================================================

        today = date.today()

        my_delayed_projects = [
            project
            for project in projects
            if (
                project.end_date is not None
                and project.end_date < today
                and project.status not in {
                    "DONE",
                    "COMPLETED",
                    "CANCELLED",
                }
            )
        ]

        # =====================================================
        # 6. PROJECT PROGRESS
        # =====================================================

        project_progress = []

        for project in projects:

            tasks = [
                task
                for task in project_tasks
                if (
                    task.project_id == project.id
                    and task.parent_id is None
                )
            ]

            if tasks:
                progress = (
                    sum(task.progress for task in tasks)
                    / len(tasks)
                )
            else:
                progress = 0.0

            project_progress.append(
                ProjectProgressItem(
                    project_id=project.id,
                    project_name=project.name,
                    progress=round(progress, 2),
                )
            )

        # =====================================================
        # 7. TASK STATUS DISTRIBUTION
        # =====================================================

        task_status = TaskStatusDistribution(
            TODO=0,
            IN_PROGRESS=0,
            IN_REVIEW=0,
            DONE=0,
            CANCELLED=0,
        )

        status_counts = {
            "TODO": 0,
            "IN_PROGRESS": 0,
            "IN_REVIEW": 0,
            "DONE": 0,
            "CANCELLED": 0,
        }

        for task in project_tasks:

            if task.status in status_counts:
                status_counts[task.status] += 1

        task_status = TaskStatusDistribution(
            **status_counts
        )

        # =====================================================
        # 8. PROJECT SUMMARY
        # =====================================================

        project_summary = []

        for project in projects:

            tasks = [
                task
                for task in project_tasks
                if (
                    task.project_id == project.id
                    and task.parent_id is None
                )
            ]

            if tasks:
                progress = (
                    sum(task.progress for task in tasks)
                    / len(tasks)
                )
            else:
                progress = 0.0

            is_delayed = (
                project.end_date is not None
                and project.end_date < today
                and project.status not in {
                    "DONE",
                    "COMPLETED",
                    "CANCELLED",
                }
            )

            project_summary.append(
                ProjectSummaryItem(
                    project_id=project.id,
                    project_name=project.name,
                    status=project.status,
                    progress=round(progress, 2),
                    due_date=project.end_date,
                    is_delayed=is_delayed,
                )
            )

        # =====================================================
        # 9. FINAL RESPONSE
        # =====================================================

        return DashboardResponse(
            summary=DashboardSummary(
                my_projects=len(projects),
                my_tasks=len(my_tasks),
                my_completed_tasks=len(my_completed_tasks),
                my_delayed_projects=len(
                    my_delayed_projects
                ),
            ),
            project_progress=project_progress,
            task_status=task_status,
            project_summary=project_summary,
        )