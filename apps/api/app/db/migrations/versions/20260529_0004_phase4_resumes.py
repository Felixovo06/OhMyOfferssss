"""phase4 resumes

Revision ID: 20260529_0004
Revises: 20260529_0003
Create Date: 2026-05-29 00:00:03

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0004"
down_revision: str | None = "20260529_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("is_scanned", sa.Boolean(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_created_by_id"), "resumes", ["created_by_id"])

    op.add_column("interview_sessions", sa.Column("resume_id", sa.String(length=36)))
    op.create_index(op.f("ix_interview_sessions_resume_id"), "interview_sessions", ["resume_id"])
    op.create_foreign_key(
        "fk_interview_sessions_resume_id_resumes",
        "interview_sessions",
        "resumes",
        ["resume_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_interview_sessions_resume_id_resumes",
        "interview_sessions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_interview_sessions_resume_id"), table_name="interview_sessions")
    op.drop_column("interview_sessions", "resume_id")
    op.drop_index(op.f("ix_resumes_created_by_id"), table_name="resumes")
    op.drop_table("resumes")

