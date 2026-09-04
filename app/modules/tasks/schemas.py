from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


TASK_STATUSES = {
    "TODO",
    "IN_PROGRESS",
    "IN_REVIEW",
    "DONE",
    "CANCELLED",
}

TASK_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "URGENT",
}


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    status: str = "TODO"

    priority: str = "MEDIUM"

    progress: int = Field(
        default=0,
        ge=0,
        le=100,
    )

    start_date: date | None = None

    due_date: date | None = None

    assignee_id: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.upper()

        if value not in TASK_STATUSES:
            raise ValueError(
                f"Invalid status. Allowed values: {', '.join(sorted(TASK_STATUSES))}"
            )

        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        value = value.upper()

        if value not in TASK_PRIORITIES:
            raise ValueError(
                f"Invalid priority. Allowed values: {', '.join(sorted(TASK_PRIORITIES))}"
            )

        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    status: str | None = None

    priority: str | None = None

    progress: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    start_date: date | None = None

    due_date: date | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.upper()

        if value not in TASK_STATUSES:
            raise ValueError(
                f"Invalid status. Allowed values: {', '.join(sorted(TASK_STATUSES))}"
            )

        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.upper()

        if value not in TASK_PRIORITIES:
            raise ValueError(
                f"Invalid priority. Allowed values: {', '.join(sorted(TASK_PRIORITIES))}"
            )

        return value


class TaskAssign(BaseModel):
    assignee_id: int | None = None


class TaskResponse(BaseModel):
    id: int
    project_id: int

    title: str
    description: str | None

    status: str
    priority: str
    progress: int

    start_date: date | None
    due_date: date | None

    assignee_id: int | None
    created_by: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
    
    
class MyTaskUpdate(BaseModel):
    status: str | None = None
    progress: int | None = Field(default=None, ge=0, le=100)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.upper()

        if value not in TASK_STATUSES:
            raise ValueError(
                f"Invalid status. Allowed values: {', '.join(sorted(TASK_STATUSES))}"
            )

        return value