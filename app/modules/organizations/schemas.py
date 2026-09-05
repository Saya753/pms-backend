from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# Organization
# =========================================================

class OrganizationCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class OrganizationUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class OrganizationResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# Role
# =========================================================

class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# Invitation
# =========================================================

class InvitationCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50,
    )

    role: str = Field(
        min_length=1,
        max_length=50,
    )


class OrganizationInvitationResponse(BaseModel):
    id: int
    organization_id: int
    invited_user_id: int
    invited_by: int

    role: RoleResponse

    status: str

    created_at: datetime
    expires_at: datetime | None
    responded_at: datetime | None

    organization_name: str
    inviter_name: str

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# Organization Members
# =========================================================

class OrganizationMemberResponse(BaseModel):
    id: int
    organization_id: int
    user_id: int

    username: str
    full_name: str | None

    role: RoleResponse

    joined_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class OrganizationMemberRoleUpdate(BaseModel):
    role: str = Field(
        min_length=1,
        max_length=50,
    )


# =========================================================
# Invitation Badge
# =========================================================

class PendingInvitationCountResponse(BaseModel):
    count: int