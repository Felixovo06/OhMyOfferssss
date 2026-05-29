"""phase6 smart interviews

Revision ID: 20260529_0006
Revises: 20260529_0005
Create Date: 2026-05-29 00:00:06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0006"
down_revision: str | None = "20260529_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("question_banks", sa.Column("target_roles", sa.JSON(), nullable=True))
    op.add_column("question_banks", sa.Column("skill_keywords", sa.JSON(), nullable=True))
    op.add_column("question_banks", sa.Column("domains", sa.JSON(), nullable=True))
    op.add_column("question_banks", sa.Column("semantic_profile_json", sa.JSON(), nullable=True))
    op.execute("UPDATE question_banks SET target_roles = '[]' WHERE target_roles IS NULL")
    op.execute("UPDATE question_banks SET skill_keywords = '[]' WHERE skill_keywords IS NULL")
    op.execute("UPDATE question_banks SET domains = '[]' WHERE domains IS NULL")
    op.execute(
        "UPDATE question_banks SET semantic_profile_json = '{}' "
        "WHERE semantic_profile_json IS NULL",
    )
    op.alter_column("question_banks", "target_roles", nullable=False)
    op.alter_column("question_banks", "skill_keywords", nullable=False)
    op.alter_column("question_banks", "domains", nullable=False)
    op.alter_column("question_banks", "semantic_profile_json", nullable=False)

    op.add_column(
        "interview_items",
        sa.Column("stage", sa.String(length=40), nullable=False, server_default="knowledge"),
    )
    op.add_column(
        "interview_items",
        sa.Column("intent", sa.String(length=120), nullable=False, server_default="知识点考察"),
    )
    op.add_column("interview_items", sa.Column("related_project", sa.String(length=200)))
    op.add_column("interview_items", sa.Column("related_skill", sa.String(length=120)))
    op.alter_column("interview_items", "stage", server_default=None)
    op.alter_column("interview_items", "intent", server_default=None)


def downgrade() -> None:
    op.drop_column("interview_items", "related_skill")
    op.drop_column("interview_items", "related_project")
    op.drop_column("interview_items", "intent")
    op.drop_column("interview_items", "stage")
    op.drop_column("question_banks", "semantic_profile_json")
    op.drop_column("question_banks", "domains")
    op.drop_column("question_banks", "skill_keywords")
    op.drop_column("question_banks", "target_roles")
