from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.repositories import ProjectRepository
from app.modules.tasks.models import Task
from app.modules.tasks.repositories import TaskRepository
from app.modules.tasks.schemas import (
    CheckpointCreate,
    CheckpointUpdate,
    MyTaskUpdate,
    TaskAssign,
    TaskCreate,
    TaskUpdate,
    TASK_PRIORITIES,
    TASK_STATUSES,
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

    # =========================================================
    # HELPERS
    # =========================================================

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
                detail=(
                    "Only Project Manager or Team Lead "
                    "can perform this action"
                ),
            )

        return member

    async def _validate_assignee(
        self,
        project_id: int,
        assignee_id: int | None,
    ) -> None:

        if assignee_id is None:
            return

        project_member = (
            await self.project_repository.get_project_member(
                project_id=project_id,
                user_id=assignee_id,
            )
        )

        if project_member is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be a member of this project",
            )

    async def _get_task_for_project(
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

    # =========================================================
    # CREATE TASK
    # =========================================================

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

        # -----------------------------------------
        # Parent validation
        # -----------------------------------------

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

            if parent_task.parent_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "A subtask cannot have another "
                        "subtask as its parent"
                    ),
                )

        # -----------------------------------------
        # Assignee
        # -----------------------------------------

        await self._validate_assignee(
            project_id=project_id,
            assignee_id=data.assignee_id,
        )

        # -----------------------------------------
        # Dates
        # -----------------------------------------

        if (
            data.start_date is not None
            and data.due_date is not None
            and data.due_date < data.start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than start date",
            )

        # -----------------------------------------
        # Duplicate title
        # -----------------------------------------

        existing_task = (
            await self.repository.get_task_by_title(
                project_id=project_id,
                title=data.title,
            )
        )

        if existing_task is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A task with this title already exists "
                    "in this project"
                ),
            )

        # -----------------------------------------
        # Create
        # -----------------------------------------

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
            estimated_minutes=data.estimated_minutes,
            assignee_id=data.assignee_id,
            created_by=current_user_id,
        )

        # -----------------------------------------
        # Activity
        # -----------------------------------------

        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task.id,
            user_id=current_user_id,
            action="TASK_CREATED",
            description=f'Task "{task.title}" was created',
        )

        return task

    # =========================================================
    # LIST PROJECT TASKS
    # =========================================================

    async def get_project_tasks(
        self,
        organization_id: int,
        project_id: int,
        current_user_id: int,
        priority: str | None = None,
        status_filter: str | None = None,
    ) -> list[Task]:

        await self._get_project_or_404(
            organization_id=organization_id,
            project_id=project_id,
        )

        await self._get_project_member(
            project_id=project_id,
            user_id=current_user_id,
        )

        if priority is not None:
            priority = priority.upper()

            if priority not in TASK_PRIORITIES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Invalid priority. Allowed values: "
                        f"{', '.join(sorted(TASK_PRIORITIES))}"
                    ),
                )

        if status_filter is not None:
            status_filter = status_filter.upper()

            if status_filter not in TASK_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Invalid status. Allowed values: "
                        f"{', '.join(sorted(TASK_STATUSES))}"
                    ),
                )

        return await self.repository.get_project_tasks(
            project_id=project_id,
            priority=priority,
            status=status_filter,
        )

    # =========================================================
    # GET TASK DETAILS
    # =========================================================

    async def get_task(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ) -> Task:

        return await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

    # =========================================================
    # UPDATE TASK
    # PM / TEAM LEAD ONLY
    # =========================================================

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

        if role_name not in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only Project Manager or Team Lead "
                    "can update task details"
                ),
            )

        # -----------------------------------------
        # Dates
        # -----------------------------------------

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

        # -----------------------------------------
        # Duplicate title
        # -----------------------------------------

        if (
            data.title is not None
            and data.title != task.title
        ):

            existing_task = (
                await self.repository.get_task_by_title(
                    project_id=project_id,
                    title=data.title,
                )
            )

            if existing_task is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "A task with this title already exists "
                        "in this project"
                    ),
                )

        old_status = task.status
        old_progress = task.progress
        old_priority = task.priority
        old_estimated_minutes = task.estimated_minutes

        task = await self.repository.update_task(
            task=task,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            progress=data.progress,
            start_date=data.start_date,
            due_date=data.due_date,
            estimated_minutes=data.estimated_minutes,
        )

        # -----------------------------------------
        # Notification: status
        # -----------------------------------------

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
                    f"from {old_status} to {task.status}"
                ),
            )

        # -----------------------------------------
        # Activity: status
        # -----------------------------------------

        if (
            data.status is not None
            and old_status != task.status
        ):

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

        # -----------------------------------------
        # Notification: progress
        # -----------------------------------------

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
                    f"from {old_progress}% to {task.progress}%"
                ),
            )

        # -----------------------------------------
        # Activity: progress
        # -----------------------------------------

        if (
            data.progress is not None
            and old_progress != task.progress
        ):

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

        # -----------------------------------------
        # Activity: priority
        # -----------------------------------------

        if (
            data.priority is not None
            and old_priority != task.priority
        ):

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_PRIORITY_CHANGED",
                description=(
                    f'Task "{task.title}" priority changed '
                    f"from {old_priority} to {task.priority}"
                ),
                old_value=old_priority,
                new_value=task.priority,
            )

        # -----------------------------------------
        # Activity: estimated time
        # -----------------------------------------

        if (
            data.estimated_minutes is not None
            and old_estimated_minutes != task.estimated_minutes
        ):

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_ESTIMATED_TIME_CHANGED",
                description=(
                    f'Task "{task.title}" estimated time changed '
                    f"from {old_estimated_minutes} minutes to "
                    f"{task.estimated_minutes} minutes"
                ),
                old_value=(
                    str(old_estimated_minutes)
                    if old_estimated_minutes is not None
                    else None
                ),
                new_value=str(task.estimated_minutes),
            )

        return task

    # =========================================================
    # ASSIGN TASK
    # =========================================================

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

        if member.project_role.name not in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Only Project Manager or Team Lead "
                    "can assign tasks"
                ),
            )

        await self._validate_assignee(
            project_id=project_id,
            assignee_id=data.assignee_id,
        )

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
                message=(
                    f'You have been assigned to task '
                    f'"{task.title}"'
                ),
            )

        if old_assignee_id != data.assignee_id:

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task.id,
                user_id=current_user_id,
                action="TASK_ASSIGNED",
                description=(
                    f'Task "{task.title}" assignment was changed'
                ),
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

    # =========================================================
    # DELETE TASK
    # =========================================================

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

    # =========================================================
    # MY TASKS
    # =========================================================

    async def get_my_tasks(
        self,
        current_user_id: int,
    ) -> list[Task]:

        return await self.repository.get_user_tasks(
            user_id=current_user_id,
        )

    # =========================================================
    # UPDATE MY TASK
    # ONLY STATUS + PROGRESS
    # =========================================================

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
        
        organization_id = (
            await self.repository.get_project_organization_id(
                task_id=task_id,
            )
        )

        if organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "Task not found or task is not assigned to you"
                ),
            )

        old_status = task.status
        old_progress = task.progress

        task = await self.repository.update_task(
            task=task,
            status=data.status,
            progress=data.progress,
        )

        if (
            data.status is not None
            and data.status != old_status
        ):

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

        if (
            data.progress is not None
            and data.progress != old_progress
        ):

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

    # =========================================================
    # GET SUBTASKS
    # =========================================================

    async def get_subtasks(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ) -> list[Task]:

        await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        return await self.repository.get_subtasks(
            project_id=project_id,
            parent_id=task_id,
        )

    # =========================================================
    # CREATE SUBTASK
    # =========================================================

    async def create_subtask(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        data: TaskCreate,
    ) -> Task:

        parent_task = await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        if parent_task.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A subtask cannot have another "
                    "subtask as its parent"
                ),
            )

        # Creating tasks is still PM / TL only.
        await self._get_project_manager_or_team_lead(
            project_id=project_id,
            user_id=current_user_id,
        )

        await self._validate_assignee(
            project_id=project_id,
            assignee_id=data.assignee_id,
        )

        if (
            data.start_date is not None
            and data.due_date is not None
            and data.due_date < data.start_date
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than start date",
            )

        existing_task = (
            await self.repository.get_task_by_title(
                project_id=project_id,
                title=data.title,
            )
        )

        if existing_task is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "A task with this title already exists "
                    "in this project"
                ),
            )

        subtask = await self.repository.create_task(
            project_id=project_id,
            parent_id=task_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            progress=data.progress,
            start_date=data.start_date,
            due_date=data.due_date,
            estimated_minutes=data.estimated_minutes,
            assignee_id=data.assignee_id,
            created_by=current_user_id,
        )

        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=subtask.id,
            user_id=current_user_id,
            action="SUBTASK_CREATED",
            description=(
                f'Subtask "{subtask.title}" was created '
                f'under task "{parent_task.title}"'
            ),
        )

        return subtask

    # =========================================================
    # CHECKPOINT HELPERS
    # =========================================================

    async def _require_task_manager_or_assignee(
        self,
        project_id: int,
        task: Task,
        user_id: int,
    ) -> None:

        member = await self._get_project_member(
            project_id=project_id,
            user_id=user_id,
        )

        role_name = member.project_role.name

        if role_name in {
            "PROJECT_MANAGER",
            "TEAM_LEAD",
        }:
            return

        if task.assignee_id == user_id:
            return

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only the task assignee, Project Manager "
                "or Team Lead can manage checkpoints"
            ),
        )

    # =========================================================
    # GET CHECKPOINTS
    # =========================================================

    async def get_checkpoints(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
    ):

        await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        return await self.repository.get_checkpoints(
            task_id=task_id,
        )

    # =========================================================
    # CREATE CHECKPOINT
    # =========================================================

    async def create_checkpoint(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        current_user_id: int,
        data: CheckpointCreate,
    ):

        task = await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        await self._require_task_manager_or_assignee(
            project_id=project_id,
            task=task,
            user_id=current_user_id,
        )

        checkpoint = await self.repository.create_checkpoint(
            task_id=task_id,
            title=data.title,
            position=data.position,
        )

        await self.activity_repository.create_log(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            user_id=current_user_id,
            action="TASK_CHECKPOINT_CREATED",
            description=(
                f'Checkpoint "{checkpoint.title}" '
                f'was created for task "{task.title}"'
            ),
        )

        return checkpoint

    # =========================================================
    # UPDATE CHECKPOINT
    # =========================================================

    async def update_checkpoint(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        checkpoint_id: int,
        current_user_id: int,
        data: CheckpointUpdate,
    ):

        task = await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        await self._require_task_manager_or_assignee(
            project_id=project_id,
            task=task,
            user_id=current_user_id,
        )

        checkpoint = await self.repository.get_checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
        )

        if checkpoint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkpoint not found",
            )

        old_completed = checkpoint.is_completed

        checkpoint = await self.repository.update_checkpoint(
            checkpoint=checkpoint,
            title=data.title,
            is_completed=data.is_completed,
            position=data.position,
        )

        if (
            data.is_completed is not None
            and old_completed != checkpoint.is_completed
        ):

            await self.activity_repository.create_log(
                organization_id=organization_id,
                project_id=project_id,
                task_id=task_id,
                user_id=current_user_id,
                action="TASK_CHECKPOINT_UPDATED",
                description=(
                    f'Checkpoint "{checkpoint.title}" '
                    f'was marked as '
                    f'{"completed" if checkpoint.is_completed else "incomplete"}'
                ),
                old_value=str(old_completed),
                new_value=str(checkpoint.is_completed),
            )

        return checkpoint

    # =========================================================
    # DELETE CHECKPOINT
    # =========================================================

    async def delete_checkpoint(
        self,
        organization_id: int,
        project_id: int,
        task_id: int,
        checkpoint_id: int,
        current_user_id: int,
    ) -> None:

        task = await self._get_task_for_project(
            organization_id=organization_id,
            project_id=project_id,
            task_id=task_id,
            current_user_id=current_user_id,
        )

        await self._require_task_manager_or_assignee(
            project_id=project_id,
            task=task,
            user_id=current_user_id,
        )

        checkpoint = await self.repository.get_checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
        )

        if checkpoint is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Checkpoint not found",
            )

        await self.repository.delete_checkpoint(
            checkpoint
        )