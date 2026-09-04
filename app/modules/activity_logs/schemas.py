from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    id: int
    organization_id: int
    project_id: int | None
    task_id: int | None
    user_id: int
    action: str
    description: str
    old_value: str | None
    new_value: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )