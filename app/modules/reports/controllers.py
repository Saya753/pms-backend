from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database.session import get_db

from app.modules.reports.excel import create_report_excel
from app.modules.reports.schemas import ReportsResponse
from app.modules.reports.services import ReportsService
from app.modules.users.models import User


reports_router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


# ==================================================
# GENERAL REPORT
# OWNER / ADMIN ONLY
# ==================================================

@reports_router.get(
    "",
    response_model=ReportsResponse,
)
async def get_general_report(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = ReportsService(db)

    return await service.get_general_report(
        current_user_id=current_user.id
    )


# ==================================================
# PROJECT REPORT
# OWNER / ADMIN / PROJECT_MANAGER
# ==================================================

@reports_router.get(
    "/projects/{project_id}",
    response_model=ReportsResponse,
)
async def get_project_report(
    project_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = ReportsService(db)

    return await service.get_project_report(
        current_user_id=current_user.id,
        project_id=project_id,
    )


# ==================================================
# GENERAL EXCEL
# OWNER / ADMIN ONLY
# ==================================================

@reports_router.get(
    "/overview/export/excel"
)
async def export_general_report_excel(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = ReportsService(db)

    projects = await service.get_general_export_projects(
        current_user_id=current_user.id
    )

    report = await service._build_report(
        projects=projects
    )

    project_ids = [
        project.id
        for project in projects
    ]

    tasks = await service.repository.get_tasks_by_project_ids(
        project_ids=project_ids
    )

    excel_file = create_report_excel(
        report=report,
        tasks=tasks,
    )

    filename = "PMS_General_Project_Report.xlsx"

    return StreamingResponse(
        excel_file,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )


# ==================================================
# PROJECT EXCEL
# OWNER / ADMIN / PROJECT_MANAGER
# ==================================================

@reports_router.get(
    "/projects/{project_id}/export/excel"
)
async def export_project_report_excel(
    project_id: int,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):

    service = ReportsService(db)

    project = await service.get_project_export(
        current_user_id=current_user.id,
        project_id=project_id,
    )

    report = await service._build_report(
        projects=[project]
    )

    tasks = await service.repository.get_tasks_by_project_ids(
        project_ids=[project.id]
    )

    excel_file = create_report_excel(
        report=report,
        tasks=tasks,
    )

    filename = (
        f"PMS_Project_{project.id}_Report.xlsx"
    )

    return StreamingResponse(
        excel_file,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{filename}"'
            )
        },
    )