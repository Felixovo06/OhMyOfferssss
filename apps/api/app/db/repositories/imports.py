from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import FeishuSource, ImportBatch, ImportItem


class ImportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_source(self, url: str, document_id: str, document_type: str) -> FeishuSource:
        source = FeishuSource(url=url, document_id=document_id, document_type=document_type)
        self.db.add(source)
        self.db.flush()
        return source

    def create_batch(
        self,
        bank_id: str,
        source_id: str,
        created_by_id: str,
        raw_blocks_json: dict,
        normalized_text: str,
        ai_result_json: dict,
        status: str,
    ) -> ImportBatch:
        batch = ImportBatch(
            bank_id=bank_id,
            source_id=source_id,
            created_by_id=created_by_id,
            raw_blocks_json=raw_blocks_json,
            normalized_text=normalized_text,
            ai_result_json=ai_result_json,
            status=status,
        )
        self.db.add(batch)
        self.db.flush()
        return batch

    def create_item(
        self,
        batch_id: str,
        question: str,
        answer: str | None,
        tags: list[str],
        difficulty_score: int,
        difficulty_label: str,
        source_block_ids: list[str],
        confidence: int,
        notes: str | None,
    ) -> ImportItem:
        item = ImportItem(
            batch_id=batch_id,
            question=question,
            answer=answer,
            tags=tags,
            difficulty_score=difficulty_score,
            difficulty_label=difficulty_label,
            source_block_ids=source_block_ids,
            confidence=confidence,
            notes=notes,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def get_batch(self, batch_id: str) -> ImportBatch | None:
        statement = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.items), selectinload(ImportBatch.source))
            .where(ImportBatch.id == batch_id)
        )
        return self.db.scalars(statement).first()

    def list_batches_for_banks(self, bank_ids: list[str]) -> list[ImportBatch]:
        if not bank_ids:
            return []
        statement = (
            select(ImportBatch)
            .options(selectinload(ImportBatch.items), selectinload(ImportBatch.source))
            .where(ImportBatch.bank_id.in_(bank_ids))
            .order_by(ImportBatch.created_at.desc())
        )
        return list(self.db.scalars(statement).unique().all())

    def list_items(self, batch_id: str) -> list[ImportItem]:
        statement = select(ImportItem).where(ImportItem.batch_id == batch_id)
        return list(self.db.scalars(statement).all())

    def get_item(self, item_id: str) -> ImportItem | None:
        return self.db.get(ImportItem, item_id)
