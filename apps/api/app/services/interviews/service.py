from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.clients.llm import (
    BankRankingResult,
    InterviewCandidate,
    InterviewPlanResult,
    InterviewStagePlanResult,
    LLMClient,
    QuestionBankCandidate,
)
from app.core.errors import AppError
from app.db.models import InterviewItem, InterviewSession, Question, QuestionBank, Resume, User
from app.db.repositories.interviews import InterviewRepository
from app.schemas.interviews import (
    InterviewAnswerCreate,
    InterviewBankRecommendation,
    InterviewCreate,
    InterviewDifficultyUpdate,
    InterviewPlanOut,
    InterviewPlanRequest,
    InterviewStagePlan,
)
from app.services.question_banks.service import QuestionBankService
from app.services.questions.service import QuestionService, difficulty_label_for_score
from app.services.resumes.service import ResumeService

INITIAL_QUESTION_BATCH_SIZE = 1


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

    def plan_interview(self, user: User, payload: InterviewPlanRequest) -> InterviewPlanOut:
        resume = self.resumes.get_resume(user, payload.resume_id) if payload.resume_id else None
        if resume:
            self._ensure_resume_ready(resume)
        target = payload.target or payload.goal
        banks = self._candidate_banks(user, payload.bank_ids)
        if not banks:
            raise AppError("NO_ACCESSIBLE_QUESTION_BANKS", "没有可用于面试的题库", status_code=422)
        ranking, plan, selected_bank_ids = self._build_interview_plan(
            banks,
            resume.summary_json if resume else None,
            target,
            payload.flow_mode,
            payload.question_count,
        )
        return InterviewPlanOut(
            flow_mode=payload.flow_mode,
            target=target,
            recommended_banks=[
                InterviewBankRecommendation(
                    bank_id=item.bank_id,
                    name=item.name,
                    score=item.score,
                    reasons=item.reasons,
                    matched_keywords=item.matched_keywords,
                    question_count=item.question_count,
                )
                for item in ranking.recommendations
            ],
            selected_bank_ids=selected_bank_ids,
            stages=[
                InterviewStagePlan(
                    stage=stage.stage,
                    title=stage.title,
                    objective=stage.objective,
                    question_count=stage.question_count,
                    focus=stage.focus,
                )
                for stage in plan.stages
            ],
            strategy=plan.strategy,
            reason=ranking.reason,
        )

    def create_session(self, user: User, payload: InterviewCreate) -> InterviewSession:
        resume = self.resumes.get_resume(user, payload.resume_id) if payload.resume_id else None
        if resume:
            self._ensure_resume_ready(resume)
        mode = payload.mode or ("custom" if resume else "normal")
        if mode == "custom" and resume is None:
            raise AppError("RESUME_REQUIRED", "客制化面试需要选择简历", status_code=422)
        target = payload.target or payload.goal
        banks = self._candidate_banks(user, payload.bank_ids)
        if not banks:
            raise AppError("NO_ACCESSIBLE_QUESTION_BANKS", "没有可用于面试的题库", status_code=422)
        available_bank_ids = [bank.id for bank in banks if bank.question_count > 0]
        if not available_bank_ids:
            raise AppError(
                "NOT_ENOUGH_QUESTIONS",
                "符合条件的候选题不足",
                status_code=422,
                details={"required": 1, "available": 0},
            )

        title = payload.title or self._default_title(payload)
        session = self.interviews.create_session(
            user.id,
            title,
            target,
            resume.id if resume else None,
            mode,
            {
                **payload.model_dump(),
                "bank_ids": payload.bank_ids,
                "flow_mode": payload.flow_mode,
                "stage_plan": [],
                "bank_recommendations": [],
            },
            "面试将在开始后按题逐步抽取，优先保证第一题快速出现。",
            "已创建轻量会话，题目会在进入面试后按上下文逐题生成。",
        )
        self.db.commit()
        return self.get_session(user, session.id)

    def start_session(self, user: User, session_id: str) -> InterviewSession:
        session = self.get_session(user, session_id)
        if session.status == "ready" and not session.items:
            self._prepare_next_item(user, session)
            session.status = "in_progress"
            self.db.commit()
        elif session.status == "ready":
            session.status = "in_progress"
            self.db.commit()
        return self.get_session(user, session.id)

    def next_question(
        self,
        user: User,
        session_id: str,
        *,
        prefetch: bool = False,
    ) -> InterviewSession:
        session = self.get_session(user, session_id)
        if session.status == "completed":
            return session
        pending_count = len([item for item in session.items if item.status == "pending"])
        if pending_count and not prefetch:
            if session.status == "ready":
                session.status = "in_progress"
                self.db.commit()
                return self.get_session(user, session.id)
            return session

        target_count = int((session.config_json or {}).get("question_count") or len(session.items))
        answered_count = len([item for item in session.items if item.status == "answered"])
        if answered_count >= target_count:
            return self.complete_session(user, session.id)
        if len(session.items) >= target_count:
            return session
        if prefetch and pending_count >= 2:
            return session

        prepared = self._prepare_next_item(user, session)
        if not prepared:
            return self.complete_session(user, session.id)
        session.status = "in_progress"
        self.db.commit()
        return self.get_session(user, session.id)

    def _prepare_next_item(self, user: User, session: InterviewSession) -> bool:
        payload = InterviewCreate.model_validate(session.config_json or {})
        self._ensure_session_plan(user, session, payload)
        payload = InterviewCreate.model_validate(session.config_json or {})
        candidates = self._candidate_questions(user, payload, payload.bank_ids)
        existing_question_ids = {item.question_id for item in session.items}
        candidates = [
            question for question in candidates if question.id not in existing_question_ids
        ]
        if not candidates:
            return False

        selection_context = self._selection_context(session)
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
            question_count=INITIAL_QUESTION_BATCH_SIZE,
            target=selection_context,
        )
        selected_id = next(
            (
                item.question_id
                for item in selection.items
                if item.question_id in {question.id for question in candidates}
            ),
            candidates[0].id,
        )
        plan_stages = [
            InterviewStagePlanResult.model_validate(stage)
            for stage in (session.config_json or {}).get("stage_plan", [])
        ]
        metadata = self._item_stage_metadata(
            plan_stages,
            [selected_id],
            candidates,
            session.resume.summary_json if session.resume else None,
        ).get(selected_id, {})
        reason_by_id = {item.question_id: item.reason for item in selection.items}
        self.interviews.create_item(
            session.id,
            selected_id,
            len(session.items) + 1,
            reason_by_id.get(selected_id, "按需补充下一题。"),
            stage=metadata.get("stage") or "knowledge",
            intent=metadata.get("intent") or "知识点考察",
            related_project=metadata.get("related_project"),
            related_skill=metadata.get("related_skill"),
        )
        session.selection_reason = selection.reason
        return True

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
                "stage": item.stage,
                "related_project": item.related_project,
                "related_skill": item.related_skill,
                "tags": item.question.tag_names,
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

    def _candidate_questions(
        self,
        user: User,
        payload: InterviewCreate,
        bank_ids: list[str],
    ) -> list[Question]:
        seen: set[str] = set()
        candidates: list[Question] = []
        tags = set(payload.tags)
        for bank_id in bank_ids:
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

    def _target_with_resume_context(
        self,
        target: str | None,
        summary: dict[str, Any] | None,
    ) -> str | None:
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

    def _candidate_banks(self, user: User, bank_ids: list[str]) -> list[QuestionBank]:
        if bank_ids:
            return [self.banks.get_accessible_bank(user, bank_id) for bank_id in bank_ids]
        return self.banks.list_banks(user)

    def _ensure_resume_ready(self, resume: Resume) -> None:
        if resume.status == "completed" and resume.summary_json:
            return
        if resume.status == "failed":
            raise AppError(
                "RESUME_NOT_READY",
                resume.error_message or "简历解析失败，无法用于智能面试",
                status_code=422,
            )
        raise AppError("RESUME_NOT_READY", "简历仍在解析中，请稍后再开始面试", status_code=422)

    def _build_interview_plan(
        self,
        banks: list[QuestionBank],
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
        question_count: int,
    ) -> tuple[BankRankingResult, InterviewPlanResult, list[str]]:
        bank_candidates = [bank_to_candidate(bank) for bank in banks]
        ranking = self.llm.rank_question_banks(
            bank_candidates,
            resume_summary=resume_summary,
            target=target,
            flow_mode=flow_mode,
        )
        selected_bank_ids = [
            item.bank_id
            for item in ranking.recommendations
            if item.question_count > 0
        ][:5]
        if not selected_bank_ids:
            selected_bank_ids = [bank.id for bank in banks if bank.question_count > 0][:5]
        selected_candidates = [
            candidate for candidate in bank_candidates if candidate.id in set(selected_bank_ids)
        ]
        plan = self.llm.plan_interview_flow(
            resume_summary=resume_summary,
            target=target,
            flow_mode=flow_mode,
            question_count=question_count,
            selected_banks=selected_candidates,
        )
        return ranking, plan, selected_bank_ids

    def _ensure_session_plan(
        self,
        user: User,
        session: InterviewSession,
        payload: InterviewCreate,
    ) -> None:
        config = dict(session.config_json or {})
        if config.get("stage_plan"):
            return
        resume_summary = session.resume.summary_json if session.resume else None
        banks = self._candidate_banks(user, payload.bank_ids)
        ranking, plan, selected_bank_ids = self._build_interview_plan(
            banks,
            resume_summary,
            session.target,
            payload.flow_mode,
            payload.question_count,
        )
        if payload.bank_ids:
            selected_bank_ids = payload.bank_ids
        config["bank_ids"] = selected_bank_ids
        config["stage_plan"] = [stage.model_dump() for stage in plan.stages]
        config["bank_recommendations"] = [item.model_dump() for item in ranking.recommendations]
        session.config_json = config
        session.strategy = plan.strategy
        session.selection_reason = ranking.reason

    def _selection_context(self, session: InterviewSession) -> str | None:
        base = self._target_with_resume_context(
            session.target,
            session.resume.summary_json if session.resume else None,
        )
        answered = [
            item
            for item in sorted(session.items, key=lambda item: item.position)
            if item.status == "answered"
        ][-3:]
        if not answered:
            return base
        history_parts = []
        for item in answered:
            feedback = item.feedback_json or {}
            score = feedback.get("score")
            action = feedback.get("next_action")
            history_parts.append(
                f"上一题：{item.question.question[:80]}；"
                f"阶段：{_stage_label(item.stage)}；"
                f"得分：{score if score is not None else '未评分'}；"
                f"建议动作：{action or 'next_question'}。"
            )
        context = " ".join(history_parts)
        return f"{base or '技术面试'}。请保持面试连贯，不要东问一句西问一句。{context}"

    def _item_stage_metadata(
        self,
        stages: list[InterviewStagePlanResult],
        selected_ids: list[str],
        candidates: list[Question],
        resume_summary: dict[str, Any] | None,
    ) -> dict[str, dict[str, str | None]]:
        candidate_by_id = {question.id: question for question in candidates}
        projects = [
            str(project.get("name") or project.get("description"))
            for project in list((resume_summary or {}).get("projects") or [])
            if isinstance(project, dict) and (project.get("name") or project.get("description"))
        ]
        metadata: dict[str, dict[str, str | None]] = {}
        cursor = 0
        for stage in stages:
            count = max(0, stage.question_count)
            for question_id in selected_ids[cursor : cursor + count]:
                question = candidate_by_id.get(question_id)
                related_skill = None
                if question:
                    related_skill = next(iter(question.tag_names), None)
                metadata[question_id] = {
                    "stage": stage.stage,
                    "intent": stage.objective[:120],
                    "related_project": projects[0][:200] if projects else None,
                    "related_skill": related_skill,
                }
            cursor += count
        for question_id in selected_ids:
            metadata.setdefault(
                question_id,
                {
                    "stage": "knowledge",
                    "intent": "知识点考察",
                    "related_project": projects[0][:200] if projects else None,
                    "related_skill": None,
                },
            )
        return metadata


def bank_to_candidate(bank: QuestionBank) -> QuestionBankCandidate:
    return QuestionBankCandidate(
        id=bank.id,
        name=bank.name,
        description=bank.description,
        default_tags=bank.default_tags,
        target_roles=bank.target_roles,
        skill_keywords=bank.skill_keywords,
        domains=bank.domains,
        question_count=bank.question_count,
    )


def _stage_label(stage: str) -> str:
    labels = {
        "project_deep_dive": "项目追问",
        "project_follow_up": "项目追问",
        "knowledge_linked": "知识点考察",
        "knowledge_probe": "知识点考察",
        "knowledge": "知识点考察",
    }
    return labels.get(stage, stage)
