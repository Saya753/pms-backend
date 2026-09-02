from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    status: str = "PLANNING"

    priority: str = "MEDIUM"

    start_date: date | None = None

    end_date: date | None = None

    budget: float | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    budget: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None
    

class ProjectResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    description: str | None
    status: str
    priority: str
    start_date: date | None
    end_date: date | None
    budget: float | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )