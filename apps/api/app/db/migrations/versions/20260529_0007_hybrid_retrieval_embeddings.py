"""hybrid retrieval embeddings

Revision ID: 20260529_0007
Revises: 20260529_0006
Create Date: 2026-05-29 00:00:07

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0007"
down_revision: str | None = "20260529_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("question_banks", sa.Column("retrieval_embedding_json", sa.JSON()))
    op.add_column("question_banks", sa.Column("retrieval_text_hash", sa.String(length=64)))
    op.add_column("questions", sa.Column("retrieval_embedding_json", sa.JSON()))
    op.add_column("questions", sa.Column("retrieval_text_hash", sa.String(length=64)))
    op.execute("UPDATE question_banks SET retrieval_embedding_json = '[]'")
    op.execute("UPDATE questions SET retrieval_embedding_json = '[]'")


def downgrade() -> None:
    op.drop_column("questions", "retrieval_text_hash")
    op.drop_column("questions", "retrieval_embedding_json")
    op.drop_column("question_banks", "retrieval_text_hash")
    op.drop_column("question_banks", "retrieval_embedding_json")
