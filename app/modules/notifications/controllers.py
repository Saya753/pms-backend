from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.notifications.schemas import (
    NotificationResponse,
    UnreadNotificationCountResponse,
)

from app.modules.notifications.services import NotificationService


router = APIRouter(
    prefix="/users/me/notifications",
    tags=["Notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
)
async def get_my_notifications(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)

    return await service.get_my_notifications(
        current_user_id=current_user.id,
    )


@router.get(
    "/unread-count",
    response_model=UnreadNotificationCountResponse,
    status_code=status.HTTP_200_OK,
)
async def get_unread_notification_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)

    count = await service.get_unread_count(
        current_user_id=current_user.id,
    )

    return {
        "count": count,
    }


@router.patch(
    "/read-all",
    status_code=status.HTTP_200_OK,
)
async def mark_all_notifications_as_read(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)

    count = await service.mark_all_as_read(
        current_user_id=current_user.id,
    )

    return {
        "message": "All notifications marked as read",
        "updated_count": count,
    }


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_notification_as_read(
    notification_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)

    return await service.mark_as_read(
        notification_id=notification_id,
        current_user_id=current_user.id,
    )