from pydantic import BaseModel, Field, ConfigDict


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

    description: str | None = None

    
class OrganizationResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int

    model_config = ConfigDict(
        from_attributes=True,
    )