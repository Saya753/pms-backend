"""add project attachment support

Revision ID: 934f3c4d02a1
Revises: b6740794a721
Create Date: 2026-09-05 14:56:12.382631

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "934f3c4d02a1"
down_revision: Union[str, Sequence[str], None] = "b6740794a721"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "attachments",
        sa.Column(
            "project_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.alter_column(
        "attachments",
        "task_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )

    op.create_index(
        op.f("ix_attachments_project_id"),
        "attachments",
        ["project_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_attachments_project_id_projects",
        "attachments",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_check_constraint(
        "ck_attachment_task_or_project",
        "attachments",
        "(task_id IS NOT NULL AND project_id IS NULL) "
        "OR "
        "(task_id IS NULL AND project_id IS NOT NULL)",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "ck_attachment_task_or_project",
        "attachments",
        type_="check",
    )

    op.drop_constraint(
        "fk_attachments_project_id_projects",
        "attachments",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_attachments_project_id"),
        table_name="attachments",
    )

    op.alter_column(
        "attachments",
        "task_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )

    op.drop_column(
        "attachments",
        "project_id",
    )