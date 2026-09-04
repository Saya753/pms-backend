from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repositories import TaskRepository
from app.modules.tasks.schemas import (
    TaskAssign,
    TaskCreate,
    TaskUpdate,
    MyTaskUpdate,
)
from app.modules.activity_logs.repositories import ActivityLogRepository
from app.modules.notifications.repositories import NotificationRepository

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = TaskRepository(db)
        self.project_repository = ProjectRepository(db)
        self.activity_repository = ActivityLogRepository(db)
        self.notification_repository = NotificationRepository(db)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    async def _get_project_or_404(
        self,
        organization_id: int,
        project_id: int,
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

        return project

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

    async def _get_project_manager_or_team_lead(
        self,
        project_id: int,
        user_id: int,
    ):
        member = await self._get_project_member(
            project_id=project_id,
            user_id=user_id,
        )

        role_name = member.project_role.name

        if role_name not in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Project Manager or Team Lead can perform this action",
            )

        return member

    async def _validate_assignee(
        self,
        project_id: int,
        assignee_id: int | None,
    ) -> None:

        if assignee_id is None:
            return

        project_member = await self.project_repository.get_project_member(
            project_id=project_id,
            user_id=assignee_id,
        )

        if project_member is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    # ---------------------------------------------------------
    # Create Task
    # ---------------------------------------------------------
    async def create_task(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        data: TaskCreate,
    ) -> Task:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_manager_or_team_lead(
            project_id=project_id,
            user_id=current_user_id,
        )

        # Validate parent task
        if data.parent_id is not None:

            parent_task = await self.repository.get_task(
                task_id=data.parent_id,
                project_id=project_id,
            )

            if parent_task is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent task must belong to this project",
                )

            # فقط Main Task می‌تواند parent باشد
            if parent_task.parent_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A subtask cannot have another subtask as its parent",
                )

        # Validate assignee
        await self._validate_assignee(
            project_id=project_id,
            assignee_id=data.assignee_id,
        )

        # Validate dates
        if (
            data.start_date is not None
            and data.due_date is not None
            and data.due_date < data.start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than start date",
            )

        # Duplicate title
        existing_task = await self.repository.get_task_by_title(
            project_id=project_id,
            title=data.title,
        )

        if existing_task is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A task with this title already exists in this project",
            )

        task = await self.repository.create_task(
            project_id=project_id,
            parent_id=data.parent_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            progress=data.progress,
            start_date=data.start_date,
            due_date=data.due_date,
            assignee_id=data.assignee_id,
            created_by=current_user_id,
        )

        # Activity Log
        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task.id,
            user_id=current_user_id,
            action="TASK_CREATED",
            description=f'Task "{task.title}" was created',
        )

        return task
                

    # ---------------------------------------------------------
    # List Project Tasks
    # ---------------------------------------------------------

    async def get_project_tasks(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
    ) -> list[Task]:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        return await self.repository.get_project_tasks(
            project_id=project_id,
        )
        
    # ---------------------------------------------------------
    # Get Task Details
    # ---------------------------------------------------------

    async def get_task(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ) -> Task:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        task = await self.repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    # ---------------------------------------------------------
    # Update Task
    # ---------------------------------------------------------

    async def update_task(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        data: TaskUpdate,
    ) -> Task:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        member = await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        task = await self.repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        role_name = member.project_role.name

        if role_name not in {"PROJECT_MANAGER", "TEAM_LEAD"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Project Manager or Team Lead can update task details",
            )

        # بررسی تاریخ‌ها
        final_start_date = (
            data.start_date
            if data.start_date is not None
            else task.start_date
        )

        final_due_date = (
            data.due_date
            if data.due_date is not None
            else task.due_date
        )

        if (
            final_start_date is not None
            and final_due_date is not None
            and final_due_date < final_start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than start date",
            )

        # بررسی title تکراری
        if data.title is not None and data.title != task.title:

            existing_task = await self.repository.get_task_by_title(
                project_id=project_id,
                title=data.title,
            )

            if existing_task is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A task with this title already exists in this project",
                )

        # ذخیره مقادیر قبلی قبل از update
        old_status = task.status
        old_progress = task.progress

        # Update Task
        task = await self.repository.update_task(
            task=task,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            progress=data.progress,
            start_date=data.start_date,
            due_date=data.due_date,
        )
        
        if (
            data.status is not None
            and old_status != task.status
            and task.assignee_id is not None
            and task.assignee_id != current_user_id
        ):
            await self.notification_repository.create_notification(
                user_id=task.assignee_id,
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                notification_type="TASK_STATUS_CHANGED",
                title="Task Status Updated",
                message=(
                    f'Task "{task.title}" status changed '
                    f'from {old_status} to {task.status}'
                ),
            )

        # Activity Log - Status
        if data.status is not None and data.status != old_status:

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_STATUS_CHANGED",
                description=(
                    f'Task "{task.title}" status changed '
                    f"from {old_status} to {task.status}"
                ),
                old_value=old_status,
                new_value=task.status,
            )
            
        if (
            data.progress is not None
            and old_progress != task.progress
            and task.assignee_id is not None
            and task.assignee_id != current_user_id
        ):
            await self.notification_repository.create_notification(
                user_id=task.assignee_id,
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                notification_type="TASK_PROGRESS_CHANGED",
                title="Task Progress Updated",
                message=(
                    f'Task "{task.title}" progress changed '
                    f'from {old_progress}% to {task.progress}%'
                ),
            )

        # Activity Log - Progress
        if data.progress is not None and data.progress != old_progress:

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_PROGRESS_CHANGED",
                description=(
                    f'Task "{task.title}" progress changed '
                    f"from {old_progress}% to {task.progress}%"
                ),
                old_value=str(old_progress),
                new_value=str(task.progress),
            )

        return task
        
    # ---------------------------------------------------------
    # Assign Task
    # ---------------------------------------------------------

    async def assign_task(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        data: TaskAssign,
    ) -> Task:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        member = await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        task = await self.repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        role_name = member.project_role.name

        if role_name not in {"PROJECT_MANAGER", "TEAM_LEAD"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Project Manager or Team Lead can assign tasks",
            )

        # Validate new assignee
        await self._validate_assignee(
            project_id=project_id,
            assignee_id=data.assignee_id,
        )

        # Save old value before update
        old_assignee_id = task.assignee_id

        task = await self.repository.assign_task(
            task=task,
            assignee_id=data.assignee_id,
        )
        
        if (
            data.assignee_id is not None
            and data.assignee_id != old_assignee_id
            and data.assignee_id != current_user_id
        ):
            await self.notification_repository.create_notification(
                user_id=data.assignee_id,
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                notification_type="TASK_ASSIGNED",
                title="New Task Assigned",
                message=f'You have been assigned to task "{task.title}"',
            )

        # Activity Log
        if old_assignee_id != data.assignee_id:
            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_ASSIGNED",
                description=f'Task "{task.title}" assignment was changed',
                old_value=(
                    str(old_assignee_id)
                    if old_assignee_id is not None
                    else None
                ),
                new_value=(
                    str(data.assignee_id)
                    if data.assignee_id is not None
                    else None
                ),
            )

        return task
                
    # ---------------------------------------------------------
    # Delete Task
    # ---------------------------------------------------------

    async def delete_task(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ) -> None:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_manager_or_team_lead(
            project_id=project_id,
            user_id=current_user_id,
        )

        task = await self.repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        await self.repository.delete_task(task)

    # ---------------------------------------------------------
    # My Tasks
    # ---------------------------------------------------------

    async def get_my_tasks(
        self,
        current_user_id: int,
    ) -> list[Task]:

        return await self.repository.get_user_tasks(
            user_id=current_user_id,
        )
        
    async def update_my_task(
        self,
        organization_id: int,
        task_id: int,
        current_user_id: int,
        data: MyTaskUpdate,
    ) -> Task:

        task = await self.repository.get_task_for_user(
            task_id=task_id,
            user_id=current_user_id,
        )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or task is not assigned to you",
            )

        # Save old values before update
        old_status = task.status
        old_progress = task.progress

        # Update only status and progress
        task = await self.repository.update_task(
            task=task,
            status=data.status,
            progress=data.progress,
        )

        # Activity Log - Status
        if data.status is not None and data.status != old_status:

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=task.project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_STATUS_CHANGED",
                description=(
                    f'Task "{task.title}" status changed '
                    f"from {old_status} to {task.status}"
                ),
                old_value=old_status,
                new_value=task.status,
            )

        # Activity Log - Progress
        if data.progress is not None and data.progress != old_progress:

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=task.project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_PROGRESS_CHANGED",
                description=(
                    f'Task "{task.title}" progress changed '
                    f"from {old_progress}% to {task.progress}%"
                ),
                old_value=str(old_progress),
                new_value=str(task.progress),
            )

        return task
    
    async def get_subtasks(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ) -> list[Task]:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        parent_task = await self.repository.get_task(
            task_id=task_id,
            project_id=project_id,
        )

        if parent_task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        # یک Subtask نمی‌تواند parent باشد
        if parent_task.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subtasks cannot have child subtasks",
            )

        return await self.repository.get_subtasks(
            project_id=project_id,
            parent_id=task_id,
        )