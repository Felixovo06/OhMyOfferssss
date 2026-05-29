from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.db.models import GroupMember, QuestionBank, User


class QuestionBankRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_accessible(self, user: User) -> list[QuestionBank]:
        member_group_ids = select(GroupMember.group_id).where(GroupMember.user_id == user.id)
        statement = (
            select(QuestionBank)
            .options(selectinload(QuestionBank.questions))
            .where(
                or_(
                    QuestionBank.created_by_id == user.id,
                    QuestionBank.group_id.in_(member_group_ids),
                ),
            )
            .order_by(QuestionBank.updated_at.desc())
        )
        return list(self.db.scalars(statement).unique().all())

    def get(self, bank_id: str) -> QuestionBank | None:
        statement = (
            select(QuestionBank)
            .options(selectinload(QuestionBank.questions))
            .where(QuestionBank.id == bank_id)
        )
        return self.db.scalars(statement).first()

    def create(
        self,
        user: User,
        name: str,
        description: str | None,
        group_id: str | None,
        default_tags: list[str],
    ) -> QuestionBank:
        bank = QuestionBank(
            name=name,
            description=description,
            group_id=group_id,
            default_tags=default_tags,
            created_by_id=user.id,
        )
        self.db.add(bank)
        self.db.flush()
        return bank

