from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Question, User
from app.db.repositories.questions import QuestionRepository
from app.schemas.questions import QuestionCreate, QuestionUpdate
from app.services.question_banks.service import QuestionBankService


class QuestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.questions = QuestionRepository(db)
        self.banks = QuestionBankService(db)

    def list_questions(
        self,
        user: User,
        bank_id: str,
        *,
        tag: str | None = None,
        difficulty_score: int | None = None,
        difficulty_label: str | None = None,
        enabled: bool | None = None,
        keyword: str | None = None,
    ) -> list[Question]:
        self.banks.get_accessible_bank(user, bank_id)
        return self.questions.list_for_bank(
            bank_id,
            tag=tag,
            difficulty_score=difficulty_score,
            difficulty_label=difficulty_label,
            enabled=enabled,
            keyword=keyword,
        )

    def create_question(self, user: User, bank_id: str, payload: QuestionCreate) -> Question:
        self.banks.get_accessible_bank(user, bank_id)
        content = payload.question or payload.content
        if not content:
            raise AppError("VALIDATION_ERROR", "题目内容不能为空", status_code=422)
        difficulty_score = payload.difficulty or payload.difficulty_score
        difficulty_label = payload.difficulty_label or difficulty_label_for_score(difficulty_score)
        enabled = payload.enabled if payload.status is None else payload.status != "disabled"
        question = self.questions.create(
            bank_id,
            content,
            payload.answer,
            difficulty_score,
            difficulty_label,
            payload.source_type,
            payload.source_block_ids,
            enabled,
        )
        self.questions.set_tags(question, payload.tags)
        self.db.commit()
        return self.get_question(user, question.id)

    def get_question(self, user: User, question_id: str) -> Question:
        question = self.questions.get(question_id)
        if question is None:
            raise AppError("QUESTION_NOT_FOUND", "题目不存在", status_code=404)
        self.banks.get_accessible_bank(user, question.bank_id)
        return question

    def update_question(self, user: User, question_id: str, payload: QuestionUpdate) -> Question:
        question = self.get_question(user, question_id)
        content = payload.question or payload.content
        if content is not None:
            question.question = content
        if payload.answer is not None:
            question.answer = payload.answer
        difficulty_score = (
            payload.difficulty if payload.difficulty is not None else payload.difficulty_score
        )
        if difficulty_score is not None:
            question.difficulty_score = difficulty_score
            question.difficulty_label = payload.difficulty_label or difficulty_label_for_score(
                difficulty_score,
            )
        elif payload.difficulty_label is not None:
            question.difficulty_label = payload.difficulty_label
        if payload.enabled is not None:
            question.enabled = payload.enabled
        if payload.status is not None:
            question.enabled = payload.status != "disabled"
        if payload.tags is not None:
            self.questions.set_tags(question, payload.tags)
        self.db.commit()
        return self.get_question(user, question_id)

    def delete_question(self, user: User, question_id: str) -> None:
        question = self.get_question(user, question_id)
        self.db.delete(question)
        self.db.commit()


def difficulty_label_for_score(score: int) -> str:
    if score <= 30:
        return "easy"
    if score <= 80:
        return "medium"
    return "hard"
