"""nullable question difficulty

Revision ID: 20260529_0005
Revises: 20260529_0004
Create Date: 2026-05-29 00:00:04

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0005"
down_revision: str | None = "20260529_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("questions", "difficulty_score", existing_type=sa.Integer(), nullable=True)
    op.alter_column(
        "questions",
        "difficulty_label",
        existing_type=sa.String(length=20),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE questions SET difficulty_score = 50 WHERE difficulty_score IS NULL")
    op.execute("UPDATE questions SET difficulty_label = 'medium' WHERE difficulty_label IS NULL")
    op.alter_column(
        "questions",
        "difficulty_label",
        existing_type=sa.String(length=20),
        nullable=False,
    )
    op.alter_column("questions", "difficulty_score", existing_type=sa.Integer(), nullable=False)
