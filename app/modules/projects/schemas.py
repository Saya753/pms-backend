from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# PROJECT CREATE
# =========================================================

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

    budget: float | None = Field(
        default=None,
        ge=0,
    )


# =========================================================
# PROJECT UPDATE
# =========================================================

class ProjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    budget: float | None = Field(
        default=None,
        ge=0,
    )

    start_date: date | None = None

    end_date: date | None = None

    status: str | None = None

    priority: str | None = None


# =========================================================
# PROJECT RESPONSE
# =========================================================

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


# =========================================================
# PROJECT ROLE
# =========================================================

class ProjectRoleResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# PROJECT MEMBER CREATE
# =========================================================

class ProjectMemberCreate(BaseModel):
    user_id: int

    role: str


# =========================================================
# PROJECT MEMBER RESPONSE
# =========================================================

class ProjectMemberResponse(BaseModel):
    id: int

    project_id: int

    user_id: int

    username: str

    full_name: str | None

    project_role: ProjectRoleResponse

    joined_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# PROJECT MEMBER ROLE UPDATE
# =========================================================

class ProjectMemberRoleUpdate(BaseModel):
    role: str


# =========================================================
# MY PROJECT
# =========================================================

class MyProjectResponse(BaseModel):
    id: int

    organization_id: int

    name: str

    description: str | None

    status: str

    priority: str

    start_date: date | None

    end_date: date | None

    budget: float | None

    role: ProjectRoleResponse

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# PROJECT LIST RESPONSE
# =========================================================

class ProjectListResponse(BaseModel):
    id: int

    organization_id: int

    organization_name: str

    name: str

    description: str | None

    status: str

    priority: str

    start_date: date | None

    end_date: date | None

    budget: float | None

    progress: float

    created_at: datetime

    updated_at: datetime


# =========================================================
# PROJECT DETAIL
# =========================================================

class ProjectDetailResponse(BaseModel):
    id: int

    organization_id: int

    organization_name: str

    name: str

    description: str | None

    status: str

    priority: str

    start_date: date | None

    end_date: date | None

    budget: float | None

    progress: float

    members: list[ProjectMemberResponse]

    created_at: datetime

    updated_at: datetime


# =========================================================
# PROJECT MEMBER SEARCH
# =========================================================

class ProjectMemberSearchResponse(BaseModel):
    user_id: int

    username: str

    full_name: str | None

    organization_id: int


# =========================================================
# PROJECT FILTER
# =========================================================

class ProjectFilterResponse(BaseModel):
    id: int

    name: str

    organization_id: int

    organization_name: str

    status: str

    priority: str

    progress: float