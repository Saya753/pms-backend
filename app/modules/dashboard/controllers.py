from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.dashboard.schemas import DashboardResponse
from app.modules.dashboard.services import DashboardService
from app.modules.users.models import User


dashboard_router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@dashboard_router.get(
    "",
    response_model=DashboardResponse,
)
async def get_dashboard(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    service = DashboardService(db)

    return await service.get_dashboard(
        current_user_id=current_user.id,
    )