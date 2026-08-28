from pydantic import BaseModel, Field


class OrganizationCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=150,
    )

    description: str | None = None
    
    
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

    model_config = {
        "from_attributes": True
    }