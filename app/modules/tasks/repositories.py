from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.tasks.models import Task, TaskCheckpoint


class TaskRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE TASK
    # =========================================================

    async def create_task(
        self,
        project_id: int,
        parent_id: int | None,
        title: str,
        description: str | None,
        status: str,
        priority: str,
        progress: int,
        start_date,
        due_date,
        estimated_minutes: int | None,
        assignee_id: int | None,
        created_by: int,
    ) -> Task:

        task = Task(
            project_id=project_id,
            parent_id=parent_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            progress=progress,
            start_date=start_date,
            due_date=due_date,
            estimated_minutes=estimated_minutes,
            assignee_id=assignee_id,
            created_by=created_by,
        )

        self.db.add(task)

        await self.db.flush()
        await self.db.commit()

        await self.db.refresh(task)

        return task

    # =========================================================
    # GET TASK
    # =========================================================

    async def get_task(
        self,
        task_id: int,
        project_id: int,
    ) -> Task | None:

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                Task.id == task_id,
                Task.project_id == project_id,
            )
        )

        return result.scalar_one_or_none()

    # =========================================================
    # GET PROJECT TASKS
    # =========================================================

    async def get_project_tasks(
        self,
        project_id: int,
        priority: str | None = None,
        status: str | None = None,
    ) -> list[Task]:

        query = (
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                Task.project_id == project_id,
                Task.parent_id.is_(None),
            )
        )

        if priority is not None:
            query = query.where(
                Task.priority == priority
            )

        if status is not None:
            query = query.where(
                Task.status == status
            )

        query = query.order_by(
            Task.created_at.desc()
        )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    # =========================================================
    # UPDATE TASK
    # =========================================================

    async def update_task(
        self,
        task: Task,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        progress: int | None = None,
        start_date=None,
        due_date=None,
        estimated_minutes: int | None = None,
    ) -> Task:

        if title is not None:
            task.title = title

        if description is not None:
            task.description = description

        if status is not None:
            task.status = status

        if priority is not None:
            task.priority = priority

        if progress is not None:
            task.progress = progress

        if start_date is not None:
            task.start_date = start_date

        if due_date is not None:
            task.due_date = due_date

        if estimated_minutes is not None:
            task.estimated_minutes = estimated_minutes

        await self.db.flush()
        await self.db.commit()

        await self.db.refresh(task)

        return task

    # =========================================================
    # ASSIGN TASK
    # =========================================================

    async def assign_task(
        self,
        task: Task,
        assignee_id: int | None,
    ) -> Task:

        task.assignee_id = assignee_id

        await self.db.flush()
        await self.db.commit()

        await self.db.refresh(task)

        return task

    # =========================================================
    # DELETE TASK
    # =========================================================

    async def delete_task(
        self,
        task: Task,
    ) -> None:

        await self.db.delete(task)

        await self.db.flush()
        await self.db.commit()

    # =========================================================
    # GET USER TASKS
    # =========================================================

    async def get_user_tasks(
        self,
        user_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                Task.assignee_id == user_id
            )
            .order_by(
                Task.due_date.asc(),
                Task.created_at.desc(),
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # GET TASK BY TITLE
    # =========================================================

    async def get_task_by_title(
        self,
        project_id: int,
        title: str,
    ) -> Task | None:

        result = await self.db.execute(
            select(Task).where(
                Task.project_id == project_id,
                Task.title == title,
            )
        )

        return result.scalar_one_or_none()

    # =========================================================
    # GET TASK FOR USER
    # =========================================================

    async def get_task_for_user(
        self,
        task_id: int,
        user_id: int,
    ) -> Task | None:

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                Task.id == task_id,
                Task.assignee_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    # =========================================================
    # GET SUBTASKS
    # =========================================================

    async def get_subtasks(
        self,
        project_id: int,
        parent_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .options(
                selectinload(Task.assignee),
                selectinload(Task.creator),
            )
            .where(
                Task.project_id == project_id,
                Task.parent_id == parent_id,
            )
            .order_by(
                Task.created_at.asc()
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # GET MAIN TASKS
    # =========================================================

    async def get_main_tasks(
        self,
        project_id: int,
    ) -> list[Task]:

        return await self.get_project_tasks(
            project_id=project_id,
        )

    # =========================================================
    # CHECKPOINTS
    # =========================================================

    async def create_checkpoint(
        self,
        task_id: int,
        title: str,
        position: int = 0,
    ) -> TaskCheckpoint:

        checkpoint = TaskCheckpoint(
            task_id=task_id,
            title=title,
            position=position,
        )

        self.db.add(checkpoint)

        await self.db.flush()
        await self.db.commit()

        await self.db.refresh(checkpoint)

        return checkpoint

    async def get_checkpoints(
        self,
        task_id: int,
    ) -> list[TaskCheckpoint]:

        result = await self.db.execute(
            select(TaskCheckpoint)
            .where(
                TaskCheckpoint.task_id == task_id
            )
            .order_by(
                TaskCheckpoint.position.asc(),
                TaskCheckpoint.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    async def get_checkpoint(
        self,
        checkpoint_id: int,
        task_id: int,
    ) -> TaskCheckpoint | None:

        result = await self.db.execute(
            select(TaskCheckpoint).where(
                TaskCheckpoint.id == checkpoint_id,
                TaskCheckpoint.task_id == task_id,
            )
        )

        return result.scalar_one_or_none()

    async def update_checkpoint(
        self,
        checkpoint: TaskCheckpoint,
        title: str | None = None,
        is_completed: bool | None = None,
        position: int | None = None,
    ) -> TaskCheckpoint:

        if title is not None:
            checkpoint.title = title

        if is_completed is not None:
            checkpoint.is_completed = is_completed

        if position is not None:
            checkpoint.position = position

        await self.db.flush()
        await self.db.commit()

        await self.db.refresh(checkpoint)

        return checkpoint

    async def delete_checkpoint(
        self,
        checkpoint: TaskCheckpoint,
    ) -> None:

        await self.db.delete(checkpoint)

        await self.db.flush()
        await self.db.commit()
        
    async def get_project_organization_id(
        self,
        task_id: int,
    ) -> int | None:

        from app.modules.projects.models import Project

        result = await self.db.execute(
            select(Project.organization_id)
            .join(
                Task,
                Task.project_id == Project.id,
            )
            .where(
                Task.id == task_id,
            )
        )

        return result.scalar_one_or_none()