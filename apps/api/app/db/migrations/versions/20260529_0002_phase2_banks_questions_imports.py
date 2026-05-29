"""phase2 banks questions imports

Revision ID: 20260529_0002
Revises: 20260529_0001
Create Date: 2026-05-29 00:00:01

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260529_0002"
down_revision: str | None = "20260529_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "question_banks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("group_id", sa.String(length=36), nullable=True),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("default_tags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_question_banks_group_id"), "question_banks", ["group_id"])

    op.create_table(
        "feishu_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("document_id", sa.String(length=200), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("last_imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_feishu_sources_document_id"), "feishu_sources", ["document_id"])

    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    op.create_table(
        "questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bank_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("difficulty_score", sa.Integer(), nullable=False),
        sa.Column("difficulty_label", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("source_block_ids", sa.JSON(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["question_banks.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["feishu_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_bank_id"), "questions", ["bank_id"])
    op.create_index(op.f("ix_questions_source_id"), "questions", ["source_id"])

    op.create_table(
        "import_batches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("bank_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("created_by_id", sa.String(length=36), nullable=False),
        sa.Column("raw_blocks_json", sa.JSON(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("ai_result_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["question_banks.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["feishu_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "question_tags",
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("question_id", "tag_id"),
        sa.UniqueConstraint("question_id", "tag_id", name="uq_question_tags_pair"),
    )

    op.create_table(
        "import_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("difficulty_score", sa.Integer(), nullable=False),
        sa.Column("difficulty_label", sa.String(length=20), nullable=False),
        sa.Column("source_block_ids", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("confirmed_question_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"]),
        sa.ForeignKeyConstraint(["confirmed_question_id"], ["questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_items_batch_id"), "import_items", ["batch_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_import_items_batch_id"), table_name="import_items")
    op.drop_table("import_items")
    op.drop_table("question_tags")
    op.drop_table("import_batches")
    op.drop_index(op.f("ix_questions_source_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_bank_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_feishu_sources_document_id"), table_name="feishu_sources")
    op.drop_table("feishu_sources")
    op.drop_index(op.f("ix_question_banks_group_id"), table_name="question_banks")
    op.drop_table("question_banks")
