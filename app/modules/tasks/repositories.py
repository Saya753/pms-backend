from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import Task


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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
            assignee_id=assignee_id,
            created_by=created_by,
        )

        self.db.add(task)

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(task)

        return task

    async def get_task(
        self,
        task_id: int,
        project_id: int,
    ) -> Task | None:

        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.project_id == project_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_project_tasks(
        self,
        project_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.parent_id.is_(None),
            )
            .order_by(Task.created_at.desc())
        )

        return list(result.scalars().all())

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

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(task)

        return task

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

    async def delete_task(
        self,
        task: Task,
    ) -> None:

        await self.db.delete(task)
        await self.db.flush()
        await self.db.commit()

    async def get_user_tasks(
        self,
        user_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .where(Task.assignee_id == user_id)
            .order_by(Task.due_date.asc(), Task.created_at.desc())
        )

        return list(result.scalars().all())
    
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
    
    async def get_task_for_user(
        self,
        task_id: int,
        user_id: int,
    ) -> Task | None:
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.assignee_id == user_id,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_subtasks(
        self,
        project_id: int,
        parent_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.parent_id == parent_id,
            )
            .order_by(Task.created_at.asc())
        )

        return list(result.scalars().all())
    
    async def get_main_tasks(
        self,
        project_id: int,
    ) -> list[Task]:

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.parent_id.is_(None),
            )
            .order_by(Task.created_at.desc())
        )

        return list(result.scalars().all())