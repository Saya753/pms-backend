from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.activity_logs.repositories import ActivityLogRepository
from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.repositories import TaskRepository


class ActivityLogService:

    def __init__(self, db: AsyncSession):
        self.db = db

        self.repository = ActivityLogRepository(db)
        self.project_repository = ProjectRepository(db)
        self.task_repository = TaskRepository(db)

    async def _validate_project_member(
        self,
        project_id: int,
        user_id: int,
    ):

        member = await self.project_repository.get_project_member(
            project_id=project_id,
            user_id=user_id,
        )

        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project",
            )

        return member

    async def get_project_logs(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ):

        project = await self.project_repository.get_project(
            project_id=project_id,
            organization_id=organization_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await self._validate_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        return await self.repository.get_project_logs(
            project_id=project_id,
        )

    async def get_task_logs(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ):

        project = await self.project_repository.get_project(
            project_id=project_id,
            organization_id=organization_id,
        )

        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        await self._validate_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        task = await self.task_repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return await self.repository.get_task_logs(
            task_id=task_id,
        )