from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import InterviewItem, InterviewSession, Question, QuestionTag


class InterviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sessions_for_user(self, user_id: str) -> list[InterviewSession]:
        statement = (
            select(InterviewSession)
            .options(selectinload(InterviewSession.items))
            .where(InterviewSession.created_by_id == user_id)
            .order_by(InterviewSession.updated_at.desc())
        )
        return list(self.db.scalars(statement).unique().all())

    def get_session(self, session_id: str) -> InterviewSession | None:
        statement = (
            select(InterviewSession)
            .options(
                selectinload(InterviewSession.items)
                .selectinload(InterviewItem.question)
                .selectinload(Question.tags)
                .selectinload(QuestionTag.tag),
                selectinload(InterviewSession.resume),
            )
            .where(InterviewSession.id == session_id)
        )
        return self.db.scalars(statement).unique().first()

    def get_item(self, item_id: str) -> InterviewItem | None:
        statement = (
            select(InterviewItem)
            .options(
                selectinload(InterviewItem.session),
                selectinload(InterviewItem.session).selectinload(InterviewSession.resume),
                selectinload(InterviewItem.question)
                .selectinload(Question.tags)
                .selectinload(QuestionTag.tag),
            )
            .where(InterviewItem.id == item_id)
        )
        return self.db.scalars(statement).unique().first()

    def create_session(
        self,
        user_id: str,
        title: str,
        target: str | None,
        resume_id: str | None,
        mode: str,
        config_json: dict,
        strategy: str,
        selection_reason: str,
    ) -> InterviewSession:
        session = InterviewSession(
            created_by_id=user_id,
            resume_id=resume_id,
            title=title,
            target=target,
            mode=mode,
            config_json=config_json,
            strategy=strategy,
            selection_reason=selection_reason,
            status="ready",
        )
        self.db.add(session)
        self.db.flush()
        return session

    def create_item(
        self,
        session_id: str,
        question_id: str,
        position: int,
        selection_reason: str,
    ) -> InterviewItem:
        item = InterviewItem(
            session_id=session_id,
            question_id=question_id,
            position=position,
            selection_reason=selection_reason,
        )
        self.db.add(item)
        self.db.flush()
        return item
