from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int

    task_id: int | None
    project_id: int | None

    uploaded_by: int

    original_filename: str
    content_type: str | None
    file_size: int

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )