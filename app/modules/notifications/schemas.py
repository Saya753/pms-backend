from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int | None
    project_id: int | None
    task_id: int | None
    invitation_id: int | None
    type: str
    title: str
    message: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadNotificationCountResponse(BaseModel):
    count: int