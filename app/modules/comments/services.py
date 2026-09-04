from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.comments.repositories import CommentRepository
from app.modules.comments.schemas import (
    CommentCreate,
    CommentUpdate,
)
from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.repositories import TaskRepository


class CommentService:

    def __init__(self, db: AsyncSession):
        self.db = db

        self.repository = CommentRepository(db)
        self.task_repository = TaskRepository(db)
        self.project_repository = ProjectRepository(db)

    async def _get_task_or_404(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
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

        task = await self.task_repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    async def _get_project_member(
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

    async def create_comment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        data: CommentCreate,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        return await self.repository.create_comment(
            task_id=task_id,
            user_id=current_user_id,
            content=data.content,
        )

    async def get_task_comments(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        return await self.repository.get_task_comments(
            task_id=task_id,
        )

    async def update_comment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        comment_id: int,
        current_user_id: int,
        data: CommentUpdate,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        comment = await self.repository.get_comment(
            comment_id=comment_id,
            task_id=task_id,
        )

        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        if comment.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only edit your own comments",
            )

        return await self.repository.update_comment(
            comment=comment,
            content=data.content,
        )

    async def delete_comment(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        comment_id: int,
        current_user_id: int,
    ):

        await self._get_task_or_404(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        comment = await self.repository.get_comment(
            comment_id=comment_id,
            task_id=task_id,
        )

        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        if comment.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

        await self.repository.delete_comment(
            comment=comment,
        )