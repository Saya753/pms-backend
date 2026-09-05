from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
# from app.modules.users.models import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # NULL = Main Task
    # ID = Subtask of that Task
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="TODO",
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(30),
        default="MEDIUM",
        nullable=False,
        index=True,
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    due_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Estimated work time in minutes
    estimated_minutes: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "title",
            name="uq_task_project_title",
        ),
    )

    # -----------------------------
    # Relationships
    # -----------------------------

    parent: Mapped["Task | None"] = relationship(
        "Task",
        remote_side=[id],
        foreign_keys=[parent_id],
        back_populates="subtasks",
    )

    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        foreign_keys=[parent_id],
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assignee_id],
        lazy="selectin",
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin",
    )

    checkpoints: Mapped[list["TaskCheckpoint"]] = relationship(
        "TaskCheckpoint",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskCheckpoint.position",
    )


class TaskCheckpoint(Base):
    __tablename__ = "task_checkpoints"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="checkpoints",
    )