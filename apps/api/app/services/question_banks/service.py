from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import ImportBatch, ImportItem, Question, QuestionBank, QuestionTag, User
from app.db.repositories.groups import GroupRepository
from app.db.repositories.question_banks import QuestionBankRepository
from app.schemas.question_banks import QuestionBankCreate, QuestionBankUpdate


class QuestionBankService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.banks = QuestionBankRepository(db)
        self.groups = GroupRepository(db)

    def list_banks(self, user: User) -> list[QuestionBank]:
        return self.banks.list_accessible(user)

    def get_accessible_bank(self, user: User, bank_id: str) -> QuestionBank:
        bank = self.banks.get(bank_id)
        if bank is None:
            raise AppError("QUESTION_BANK_NOT_FOUND", "题库不存在", status_code=404)
        if not self._can_access(user, bank):
            raise AppError("FORBIDDEN", "无权访问该题库", status_code=403)
        return bank

    def create_bank(self, user: User, payload: QuestionBankCreate) -> QuestionBank:
        if payload.group_id:
            member = self.groups.get_member(payload.group_id, user.id)
            if member is None:
                raise AppError("FORBIDDEN", "无权在该小组创建题库", status_code=403)
            if member.role != "owner":
                raise AppError("FORBIDDEN", "只有小组 owner 可以创建小组题库", status_code=403)
        bank = self.banks.create(
            user,
            payload.name,
            payload.description,
            payload.group_id,
            compact_strings(payload.default_tags),
            compact_strings([*payload.target_roles, *payload.target_positions]),
            compact_strings(payload.skill_keywords),
            compact_strings([*payload.domains, *payload.domain_tags]),
            payload.semantic_profile,
        )
        self.db.commit()
        self.db.refresh(bank)
        return self.get_accessible_bank(user, bank.id)

    def update_bank(
        self,
        user: User,
        bank_id: str,
        payload: QuestionBankUpdate,
    ) -> QuestionBank:
        bank = self.get_accessible_bank(user, bank_id)
        self._require_bank_owner(user, bank)
        if payload.name is not None:
            bank.name = payload.name
        if payload.description is not None:
            bank.description = payload.description
        if payload.default_tags is not None:
            bank.default_tags = compact_strings(payload.default_tags)
        if payload.target_roles is not None:
            bank.target_roles = compact_strings(payload.target_roles)
        if payload.target_positions is not None:
            bank.target_roles = compact_strings(payload.target_positions)
        if payload.skill_keywords is not None:
            bank.skill_keywords = compact_strings(payload.skill_keywords)
        if payload.domains is not None:
            bank.domains = compact_strings(payload.domains)
        if payload.domain_tags is not None:
            bank.domains = compact_strings(payload.domain_tags)
        if payload.semantic_profile is not None:
            bank.semantic_profile_json = payload.semantic_profile
        self.db.commit()
        return self.get_accessible_bank(user, bank.id)

    def delete_bank(self, user: User, bank_id: str) -> None:
        bank = self.get_accessible_bank(user, bank_id)
        self._require_bank_owner(user, bank)
        question_ids = select(Question.id).where(Question.bank_id == bank.id)
        batch_ids = select(ImportBatch.id).where(ImportBatch.bank_id == bank.id)
        self.db.execute(
            update(ImportItem)
            .where(ImportItem.confirmed_question_id.in_(question_ids))
            .values(confirmed_question_id=None)
            .execution_options(synchronize_session=False),
        )
        self.db.execute(
            delete(ImportItem)
            .where(ImportItem.batch_id.in_(batch_ids))
            .execution_options(synchronize_session=False),
        )
        self.db.execute(
            delete(ImportBatch)
            .where(ImportBatch.bank_id == bank.id)
            .execution_options(synchronize_session=False),
        )
        self.db.execute(
            delete(QuestionTag)
            .where(QuestionTag.question_id.in_(question_ids))
            .execution_options(synchronize_session=False),
        )
        self.db.execute(
            delete(Question)
            .where(Question.bank_id == bank.id)
            .execution_options(synchronize_session=False),
        )
        self.db.execute(
            delete(QuestionBank)
            .where(QuestionBank.id == bank.id)
            .execution_options(synchronize_session=False),
        )
        self.db.commit()

    def _can_access(self, user: User, bank: QuestionBank) -> bool:
        if bank.created_by_id == user.id:
            return True
        return bool(bank.group_id and self.groups.get_member(bank.group_id, user.id))

    def _require_bank_owner(self, user: User, bank: QuestionBank) -> None:
        if bank.created_by_id == user.id:
            return
        if bank.group_id:
            member = self.groups.get_member(bank.group_id, user.id)
            if member and member.role == "owner":
                return
        raise AppError("FORBIDDEN", "无权修改该题库", status_code=403)


def compact_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value.strip() for value in values if value.strip()))
