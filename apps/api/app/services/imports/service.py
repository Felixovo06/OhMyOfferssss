from typing import Any

from sqlalchemy.orm import Session

from app.clients.feishu import FeishuClient
from app.clients.llm import LLMClient
from app.core.errors import AppError
from app.db.models import ImportBatch, ImportItem, QuestionBank, User
from app.db.repositories.imports import ImportRepository
from app.schemas.imports import FeishuImportRequest, ImportItemUpdate
from app.schemas.question_banks import QuestionBankCreate
from app.schemas.questions import QuestionCreate
from app.services.question_banks.service import QuestionBankService
from app.services.questions.service import QuestionService


class ImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.imports = ImportRepository(db)
        self.banks = QuestionBankService(db)
        self.questions = QuestionService(db)
        self.feishu = FeishuClient()
        self.llm = LLMClient()

    def import_feishu(self, user: User, payload: FeishuImportRequest) -> ImportBatch:
        bank_id = payload.bank_id or self._create_default_import_bank(user).id
        self.banks.get_accessible_bank(user, bank_id)
        document_type, document_id = self.feishu.parse_document_url(payload.url)
        source = self.imports.create_source(payload.url, document_id, document_type)
        raw_blocks = self.feishu.fetch_document_blocks(document_id, document_type)
        normalized_text = normalize_feishu_blocks(raw_blocks)
        extracted = self.llm.extract_questions_from_text(normalized_text)
        batch = self.imports.create_batch(
            bank_id,
            source.id,
            user.id,
            raw_blocks,
            normalized_text,
            extracted.model_dump(),
            "pending_confirmation",
        )
        for item in extracted.items:
            self.imports.create_item(
                batch.id,
                item.question,
                item.answer,
                item.tags,
                item.difficulty_score,
                item.difficulty_label,
                item.source_block_ids,
                round(item.confidence * 100),
                item.notes,
            )
        self.db.commit()
        return self.get_batch_for_user(user, batch.id)

    def list_batches(self, user: User) -> list[ImportBatch]:
        banks = self.banks.list_banks(user)
        return self.imports.list_batches_for_banks([bank.id for bank in banks])

    def get_batch_for_user(self, user: User, batch_id: str) -> ImportBatch:
        batch = self.imports.get_batch(batch_id)
        if batch is None:
            raise AppError("IMPORT_BATCH_NOT_FOUND", "导入批次不存在", status_code=404)
        self.banks.get_accessible_bank(user, batch.bank_id)
        return batch

    def list_items(self, user: User, batch_id: str) -> list[ImportItem]:
        self.get_batch_for_user(user, batch_id)
        return self.imports.list_items(batch_id)

    def update_item(self, user: User, item_id: str, payload: ImportItemUpdate) -> ImportItem:
        item = self.imports.get_item(item_id)
        if item is None:
            raise AppError("IMPORT_ITEM_NOT_FOUND", "导入项不存在", status_code=404)
        self.get_batch_for_user(user, item.batch_id)
        if payload.question is not None:
            item.question = payload.question
        if payload.answer is not None:
            item.answer = payload.answer
        if payload.tags is not None:
            item.tags = payload.tags
        if payload.difficulty_score is not None:
            item.difficulty_score = payload.difficulty_score
        if payload.difficulty_label is not None:
            item.difficulty_label = payload.difficulty_label
        if payload.status is not None:
            if payload.status not in {"pending", "discarded"}:
                raise AppError("INVALID_IMPORT_ITEM_STATUS", "导入项状态无效", status_code=422)
            item.status = payload.status
        self.db.commit()
        return item

    def reject_item(self, user: User, item_id: str) -> ImportItem:
        return self.update_item(user, item_id, ImportItemUpdate(status="discarded"))

    def confirm_item(self, user: User, item_id: str) -> tuple[ImportItem, str | None]:
        item = self.imports.get_item(item_id)
        if item is None:
            raise AppError("IMPORT_ITEM_NOT_FOUND", "导入项不存在", status_code=404)
        batch = self.get_batch_for_user(user, item.batch_id)
        if item.status != "pending":
            return item, item.confirmed_question_id
        question = self.questions.create_question(
            user,
            batch.bank_id,
            QuestionCreate(
                question=item.question,
                answer=item.answer,
                tags=item.tags,
                difficulty_score=item.difficulty_score,
                difficulty_label=item.difficulty_label,
                source_type="feishu_import",
                source_block_ids=item.source_block_ids,
            ),
        )
        question.source_id = batch.source_id
        item.status = "confirmed"
        item.confirmed_question_id = question.id
        self.db.commit()
        return item, question.id

    def confirm_batch(self, user: User, batch_id: str) -> tuple[int, list[str]]:
        batch = self.get_batch_for_user(user, batch_id)
        question_ids: list[str] = []
        for item in batch.items:
            if item.status != "pending":
                continue
            question = self.questions.create_question(
                user,
                batch.bank_id,
                QuestionCreate(
                    question=item.question,
                    answer=item.answer,
                    tags=item.tags,
                    difficulty_score=item.difficulty_score,
                    difficulty_label=item.difficulty_label,
                    source_type="feishu_import",
                    source_block_ids=item.source_block_ids,
                ),
            )
            question.source_id = batch.source_id
            item.status = "confirmed"
            item.confirmed_question_id = question.id
            question_ids.append(question.id)
        batch.status = "confirmed"
        self.db.commit()
        return len(question_ids), question_ids

    def _create_default_import_bank(self, user: User) -> QuestionBank:
        return self.banks.create_bank(
            user,
            QuestionBankCreate(
                name="飞书导入默认题库",
                description="未选择题库时自动创建",
                default_tags=["飞书导入"],
            ),
        )


def normalize_feishu_blocks(raw_blocks: dict[str, Any]) -> str:
    lines: list[str] = []
    for block in raw_blocks.get("blocks", []):
        block_id = str(block.get("block_id", ""))
        block_type = str(block.get("block_type", "text"))
        text = extract_block_text(block)
        if not text:
            continue
        prefix = "#" if "heading1" in block_type else "##" if "heading2" in block_type else ""
        line = f"{prefix} {text}".strip() if prefix else text
        lines.append(f"[{block_id}] {line}" if block_id else line)
    return "\n".join(lines)


def extract_block_text(block: dict[str, Any]) -> str:
    if isinstance(block.get("text"), str):
        return block["text"]
    for key in ("text", "heading1", "heading2", "paragraph", "code"):
        value = block.get(key)
        if isinstance(value, dict):
            elements = value.get("elements") or []
            parts: list[str] = []
            for element in elements:
                text_run = element.get("text_run") if isinstance(element, dict) else None
                if isinstance(text_run, dict):
                    parts.append(str(text_run.get("content", "")))
            if parts:
                return "".join(parts)
    return ""
