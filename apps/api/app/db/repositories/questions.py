from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Question, QuestionTag, Tag


class QuestionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_bank(
        self,
        bank_id: str,
        *,
        tag: str | None = None,
        difficulty_score: int | None = None,
        difficulty_label: str | None = None,
        enabled: bool | None = None,
        keyword: str | None = None,
    ) -> list[Question]:
        statement = (
            select(Question)
            .options(selectinload(Question.tags).selectinload(QuestionTag.tag))
            .where(Question.bank_id == bank_id)
            .order_by(Question.updated_at.desc())
        )
        if difficulty_score is not None:
            statement = statement.where(Question.difficulty_score == difficulty_score)
        if difficulty_label:
            statement = statement.where(Question.difficulty_label == difficulty_label)
        if enabled is not None:
            statement = statement.where(Question.enabled == enabled)
        if keyword:
            statement = statement.where(Question.question.ilike(f"%{keyword}%"))
        questions = list(self.db.scalars(statement).unique().all())
        if tag:
            questions = [question for question in questions if tag in question.tag_names]
        return questions

    def get(self, question_id: str) -> Question | None:
        statement = (
            select(Question)
            .options(selectinload(Question.tags).selectinload(QuestionTag.tag))
            .where(Question.id == question_id)
        )
        return self.db.scalars(statement).first()

    def create(
        self,
        bank_id: str,
        question: str,
        answer: str | None,
        difficulty_score: int | None,
        difficulty_label: str | None,
        source_type: str,
        source_block_ids: list[str],
        enabled: bool,
        source_id: str | None = None,
    ) -> Question:
        entity = Question(
            bank_id=bank_id,
            source_id=source_id,
            question=question,
            answer=answer,
            difficulty_score=difficulty_score,
            difficulty_label=difficulty_label,
            source_type=source_type,
            source_block_ids=source_block_ids,
            enabled=enabled,
        )
        self.db.add(entity)
        self.db.flush()
        return entity

    def list_tags(self) -> list[Tag]:
        return list(self.db.scalars(select(Tag).order_by(Tag.name.asc())).all())

    def get_or_create_tag(self, name: str) -> Tag:
        normalized = name.strip()
        statement = select(Tag).where(Tag.name == normalized)
        tag = self.db.scalars(statement).first()
        if tag:
            return tag
        tag = Tag(name=normalized)
        self.db.add(tag)
        self.db.flush()
        return tag

    def set_tags(self, question: Question, tag_names: list[str]) -> None:
        question.tags.clear()
        for name in dict.fromkeys(tag.strip() for tag in tag_names if tag.strip()):
            tag = self.get_or_create_tag(name)
            question.tags.append(QuestionTag(tag=tag))
        self.db.flush()
