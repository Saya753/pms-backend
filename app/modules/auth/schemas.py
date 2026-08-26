from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    username: str = Field(
        min_length=3,
        max_length=50,
    )

    phone: str = Field(
        min_length=10,
        max_length=20,
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class RegisterResponse(BaseModel):

    id: int
    full_name: str | None
    username: str
    phone: str
    email: EmailStr
    status: bool

    model_config = {
        "from_attributes": True
    }