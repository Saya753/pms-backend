from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


def _style_header(row):
    fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    font = Font(
        bold=True,
        color="FFFFFF",
    )

    for cell in row:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )


def _auto_width(ws):

    for column_cells in ws.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            if cell.value is not None:

                length = len(
                    str(cell.value)
                )

                if length > max_length:
                    max_length = length

        ws.column_dimensions[
            column_letter
        ].width = min(
            max_length + 3,
            40,
        )


def _format_percentage(cell):
    cell.number_format = '0.00"%"'


def create_report_excel(report, tasks):

    workbook = Workbook()

    # =========================================================
    # Summary
    # =========================================================

    ws = workbook.active
    ws.title = "Summary"

    ws["A1"] = "Project Management System - Reports"
    ws["A1"].font = Font(
        bold=True,
        size=16,
    )

    ws["A3"] = "Total Projects"
    ws["B3"] = report.summary.total_projects

    ws["A4"] = "Total Tasks"
    ws["B4"] = report.summary.total_tasks

    ws["A5"] = "Completed Tasks"
    ws["B5"] = report.summary.completed_tasks

    ws["A6"] = "Average Project Progress"
    ws["B6"] = report.summary.average_project_progress
    _format_percentage(ws["B6"])

    ws["A8"] = "Performance Summary"

    ws["A9"] = "Task Completion Rate"
    ws["B9"] = report.performance.task_completion_rate
    _format_percentage(ws["B9"])

    ws["A10"] = "Average Project Progress"
    ws["B10"] = report.performance.average_project_progress
    _format_percentage(ws["B10"])

    # =========================================================
    # Project Portfolio
    # =========================================================

    ws_projects = workbook.create_sheet(
        "سبد پروژه‌ها"
    )

    headers = [
        "ردیف",
        "نام پروژه",
        "وضعیت",
        "درصد پیشرفت",
        "کل وظایف",
        "وظایف تکمیل شده",
        "نرخ تکمیل وظایف",
        "تاریخ پایان",
        "تاخیر",
    ]

    ws_projects.append(headers)
    _style_header(ws_projects[1])

    for index, project in enumerate(
        report.projects,
        start=1,
    ):

        ws_projects.append([
            index,
            project.project_name,
            project.status,
            project.progress,
            project.total_tasks,
            project.completed_tasks,
            project.task_completion_rate,
            project.due_date,
            "بله" if project.is_delayed else "خیر",
        ])

        _format_percentage(
            ws_projects.cell(
                row=ws_projects.max_row,
                column=4,
            )
        )

        _format_percentage(
            ws_projects.cell(
                row=ws_projects.max_row,
                column=7,
            )
        )

    # =========================================================
    # Task Database
    # =========================================================

    ws_tasks = workbook.create_sheet(
        "Database_فعالیت‌ها"
    )

    task_headers = [
        "پروژه",
        "فعالیت",
        "وضعیت",
        "اولویت",
        "شروع",
        "پایان",
        "درصد پیشرفت",
        "مسئول",
    ]

    ws_tasks.append(task_headers)
    _style_header(ws_tasks[1])

    project_name_map = {
        project.project_id: project.project_name
        for project in report.projects
    }

    for task in tasks:

        ws_tasks.append([
            project_name_map.get(
                task.project_id,
                "",
            ),
            task.title,
            task.status,
            task.priority,
            task.start_date,
            task.due_date,
            task.progress,
            task.assignee_id,
        ])

        _format_percentage(
            ws_tasks.cell(
                row=ws_tasks.max_row,
                column=7,
            )
        )

    # =========================================================
    # One sheet per project
    # =========================================================

    for project in report.projects:

        sheet_name = (
            project.project_name
            .replace("/", "-")
            .replace("\\", "-")
            .replace("*", "")
            .replace("?", "")
            .replace("[", "")
            .replace("]", "")
            .replace(":", "")
        )

        sheet_name = sheet_name[:31]

        if not sheet_name:
            sheet_name = f"Project-{project.project_id}"

        if sheet_name in workbook.sheetnames:
            sheet_name = (
                f"P-{project.project_id}"
            )

        ws_project = workbook.create_sheet(
            sheet_name
        )

        ws_project["A1"] = "Project"
        ws_project["B1"] = project.project_name

        ws_project["A2"] = "Status"
        ws_project["B2"] = project.status

        ws_project["A3"] = "Progress"
        ws_project["B3"] = project.progress
        _format_percentage(ws_project["B3"])

        ws_project["A4"] = "Total Tasks"
        ws_project["B4"] = project.total_tasks

        ws_project["A5"] = "Completed Tasks"
        ws_project["B5"] = project.completed_tasks

        ws_project["A6"] = "Task Completion Rate"
        ws_project["B6"] = project.task_completion_rate
        _format_percentage(ws_project["B6"])

        ws_project["A7"] = "Due Date"
        ws_project["B7"] = project.due_date

        ws_project["A8"] = "Delayed"
        ws_project["B8"] = (
            "Yes"
            if project.is_delayed
            else "No"
        )

        project_tasks = [
            task
            for task in tasks
            if task.project_id == project.project_id
        ]

        ws_project["A10"] = "Tasks"
        ws_project["A10"].font = Font(
            bold=True,
            size=14,
        )

        project_task_headers = [
            "Title",
            "Status",
            "Priority",
            "Start Date",
            "Due Date",
            "Progress",
            "Assignee ID",
        ]

        ws_project.append(
            project_task_headers
        )

        _style_header(
            ws_project[11]
        )

        for task in project_tasks:

            ws_project.append([
                task.title,
                task.status,
                task.priority,
                task.start_date,
                task.due_date,
                task.progress,
                task.assignee_id,
            ])

            _format_percentage(
                ws_project.cell(
                    row=ws_project.max_row,
                    column=6,
                )
            )

    # =========================================================
    # General formatting
    # =========================================================

    thin = Side(
        style="thin",
        color="D9E2F3",
    )

    for worksheet in workbook.worksheets:

        worksheet.freeze_panes = "A2"

        for row in worksheet.iter_rows():

            for cell in row:

                cell.alignment = Alignment(
                    vertical="center",
                )

                cell.border = Border(
                    bottom=thin
                )

        _auto_width(worksheet)

    # =========================================================
    # Save to memory
    # =========================================================

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return output