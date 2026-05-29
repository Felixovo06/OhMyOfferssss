"""phase3 interviews

Revision ID: 20260529_0003
Revises: 20260529_0002
Create Date: 2026-05-29 00:00:02

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0003"
down_revision: str | None = "20260529_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("target", sa.String(length=300), nullable=True),
        sa.Column("config_json", sa.JSON(), nullable=False),
        sa.Column("strategy", sa.Text(), nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_sessions_created_by_id"),
        "interview_sessions",
        ["created_by_id"],
    )

    op.create_table(
        "interview_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("feedback_json", sa.JSON(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_items_question_id"), "interview_items", ["question_id"])
    op.create_index(op.f("ix_interview_items_session_id"), "interview_items", ["session_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_items_session_id"), table_name="interview_items")
    op.drop_index(op.f("ix_interview_items_question_id"), table_name="interview_items")
    op.drop_table("interview_items")
    op.drop_index(
        op.f("ix_interview_sessions_created_by_id"),
        table_name="interview_sessions",
    )
    op.drop_table("interview_sessions")

