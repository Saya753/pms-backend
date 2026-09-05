from datetime import date

from pydantic import BaseModel


class ReportSummary(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    average_project_progress: float


class ProjectReportItem(BaseModel):
    project_id: int
    project_name: str
    status: str
    progress: float
    total_tasks: int
    completed_tasks: int
    task_completion_rate: float
    due_date: date | None
    is_delayed: bool


class PerformanceSummary(BaseModel):
    task_completion_rate: float
    average_project_progress: float


class ReportsResponse(BaseModel):
    summary: ReportSummary
    projects: list[ProjectReportItem]
    performance: PerformanceSummary