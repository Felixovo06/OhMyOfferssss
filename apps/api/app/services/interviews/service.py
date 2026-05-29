from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.clients.llm import InterviewCandidate, LLMClient
from app.core.errors import AppError
from app.db.models import InterviewItem, InterviewSession, Question, User
from app.db.repositories.interviews import InterviewRepository
from app.schemas.interviews import InterviewAnswerCreate, InterviewCreate, InterviewDifficultyUpdate
from app.services.question_banks.service import QuestionBankService
from app.services.questions.service import QuestionService, difficulty_label_for_score
from app.services.resumes.service import ResumeService


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.interviews = InterviewRepository(db)
        self.banks = QuestionBankService(db)
        self.questions = QuestionService(db)
        self.resumes = ResumeService(db)
        self.llm = LLMClient()

    def list_sessions(self, user: User) -> list[InterviewSession]:
        return self.interviews.list_sessions_for_user(user.id)

    def get_session(self, user: User, session_id: str) -> InterviewSession:
        session = self.interviews.get_session(session_id)
        if session is None:
            raise AppError("INTERVIEW_NOT_FOUND", "面试会话不存在", status_code=404)
        if session.created_by_id != user.id:
            raise AppError("FORBIDDEN", "无权访问该面试会话", status_code=403)
        return session

    def create_session(self, user: User, payload: InterviewCreate) -> InterviewSession:
        resume = self.resumes.get_resume(user, payload.resume_id) if payload.resume_id else None
        mode = payload.mode or ("custom" if resume else "normal")
        if mode == "custom" and resume is None:
            raise AppError("RESUME_REQUIRED", "客制化面试需要选择简历", status_code=422)
        target = payload.target or payload.goal
        llm_target = self._target_with_resume_context(
            target,
            resume.summary_json if resume else None,
        )
        candidates = self._candidate_questions(user, payload)
        if len(candidates) < payload.question_count:
            raise AppError(
                "NOT_ENOUGH_QUESTIONS",
                "符合条件的候选题不足",
                status_code=422,
                details={"required": payload.question_count, "available": len(candidates)},
            )

        selection = self.llm.select_interview_questions(
            [
                InterviewCandidate(
                    id=question.id,
                    question=question.question,
                    answer=question.answer,
                    tags=question.tag_names,
                    difficulty_score=question.difficulty_score or 50,
                    difficulty_label=question.difficulty_label or "medium",
                )
                for question in candidates
            ],
            question_count=payload.question_count,
            target=llm_target,
        )
        candidate_by_id = {question.id: question for question in candidates}
        selected_ids = [
            item.question_id
            for item in selection.items
            if item.question_id in candidate_by_id
        ][: payload.question_count]
        if len(selected_ids) < payload.question_count:
            for question in candidates:
                if question.id not in selected_ids:
                    selected_ids.append(question.id)
                if len(selected_ids) == payload.question_count:
                    break

        title = payload.title or self._default_title(payload)
        session = self.interviews.create_session(
            user.id,
            title,
            target,
            resume.id if resume else None,
            mode,
            payload.model_dump(),
            selection.strategy,
            selection.reason,
        )
        reason_by_id = {item.question_id: item.reason for item in selection.items}
        for index, question_id in enumerate(selected_ids, start=1):
            self.interviews.create_item(
                session.id,
                question_id,
                index,
                reason_by_id.get(question_id, "规则兜底补足题目。"),
            )
        self.db.commit()
        return self.get_session(user, session.id)

    def answer_item(
        self,
        user: User,
        item_id: str,
        payload: InterviewAnswerCreate,
    ) -> InterviewItem:
        item = self.interviews.get_item(item_id)
        if item is None:
            raise AppError("INTERVIEW_ITEM_NOT_FOUND", "面试题不存在", status_code=404)
        if item.session.created_by_id != user.id:
            raise AppError("FORBIDDEN", "无权回答该面试题", status_code=403)

        feedback = self.llm.score_interview_answer(
            question=item.question.question,
            reference_answer=item.question.answer,
            user_answer=payload.answer,
            target=self._target_with_resume_context(
                item.session.target,
                item.session.resume.summary_json if item.session.resume else None,
            ),
        )
        difficulty_score = (
            payload.difficulty if payload.difficulty is not None else payload.difficulty_score
        )
        if difficulty_score is not None:
            item.question.difficulty_score = difficulty_score
            item.question.difficulty_label = difficulty_label_for_score(difficulty_score)
        item.answer = payload.answer
        item.feedback_json = feedback.model_dump()
        item.status = "answered"
        item.answered_at = datetime.now(UTC)
        if item.session.status == "ready":
            item.session.status = "in_progress"
        self.db.commit()
        refreshed = self.interviews.get_item(item.id)
        if refreshed is None:
            raise AppError("INTERVIEW_ITEM_NOT_FOUND", "面试题不存在", status_code=404)
        return refreshed

    def update_item_difficulty(
        self,
        user: User,
        item_id: str,
        payload: InterviewDifficultyUpdate,
    ) -> InterviewItem:
        item = self.interviews.get_item(item_id)
        if item is None:
            raise AppError("INTERVIEW_ITEM_NOT_FOUND", "面试题不存在", status_code=404)
        if item.session.created_by_id != user.id:
            raise AppError("FORBIDDEN", "无权修改该面试题", status_code=403)
        difficulty_score = (
            payload.difficulty if payload.difficulty is not None else payload.difficulty_score
        )
        if difficulty_score is None:
            item.question.difficulty_score = None
            item.question.difficulty_label = None
        else:
            item.question.difficulty_score = difficulty_score
            item.question.difficulty_label = difficulty_label_for_score(difficulty_score)
        self.db.commit()
        refreshed = self.interviews.get_item(item.id)
        if refreshed is None:
            raise AppError("INTERVIEW_ITEM_NOT_FOUND", "面试题不存在", status_code=404)
        return refreshed

    def complete_session(self, user: User, session_id: str) -> InterviewSession:
        session = self.get_session(user, session_id)
        answered_items = [
            {
                "question": item.question.question,
                "answer": item.answer,
                "feedback": item.feedback_json,
            }
            for item in session.items
            if item.status == "answered"
        ]
        if not answered_items:
            raise AppError(
                "INTERVIEW_HAS_NO_ANSWERS",
                "请至少回答一道题后再结束面试",
                status_code=422,
            )
        summary = self.llm.summarize_interview(
            target=session.target,
            answered_items=answered_items,
        )
        session.summary_json = summary.model_dump()
        session.status = "completed"
        session.completed_at = datetime.now(UTC)
        self.db.commit()
        return self.get_session(user, session.id)

    def _candidate_questions(self, user: User, payload: InterviewCreate) -> list[Question]:
        seen: set[str] = set()
        candidates: list[Question] = []
        tags = set(payload.tags)
        for bank_id in payload.bank_ids:
            self.banks.get_accessible_bank(user, bank_id)
            questions = self.questions.list_questions(user, bank_id, enabled=True)
            for question in questions:
                if question.id in seen:
                    continue
                if (
                    payload.difficulty_min is not None
                    and question.difficulty_score is not None
                    and question.difficulty_score < payload.difficulty_min
                ):
                    continue
                if (
                    payload.difficulty_max is not None
                    and question.difficulty_score is not None
                    and question.difficulty_score > payload.difficulty_max
                ):
                    continue
                if (
                    (payload.difficulty_min is not None or payload.difficulty_max is not None)
                    and question.difficulty_score is None
                ):
                    continue
                if tags and not tags.intersection(question.tag_names):
                    continue
                seen.add(question.id)
                candidates.append(question)
        return candidates

    def _default_title(self, payload: InterviewCreate) -> str:
        target = payload.target or payload.goal
        suffix = f" - {target}" if target else ""
        interview_type = "客制化" if payload.mode == "custom" or payload.resume_id else "普通"
        return f"{interview_type}面试{suffix}"

    def _target_with_resume_context(self, target: str | None, summary: dict | None) -> str | None:
        if not summary:
            return target
        skills = "、".join(summary.get("skills") or [])
        directions = "；".join(summary.get("follow_up_directions") or [])
        parts = [target or "客制化面试"]
        if skills:
            parts.append(f"候选人技能：{skills}")
        if directions:
            parts.append(f"简历追问方向：{directions}")
        return "。".join(parts)
