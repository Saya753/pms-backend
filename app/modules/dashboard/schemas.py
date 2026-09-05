from datetime import date

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    my_projects: int
    my_tasks: int
    my_completed_tasks: int
    my_delayed_projects: int


class ProjectProgressItem(BaseModel):
    project_id: int
    project_name: str
    progress: float


class TaskStatusDistribution(BaseModel):
    TODO: int
    IN_PROGRESS: int
    IN_REVIEW: int
    DONE: int
    CANCELLED: int


class ProjectSummaryItem(BaseModel):
    project_id: int
    project_name: str
    status: str
    progress: float
    due_date: date | None
    is_delayed: bool


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    project_progress: list[ProjectProgressItem]
    task_status: TaskStatusDistribution
    project_summary: list[ProjectSummaryItem]