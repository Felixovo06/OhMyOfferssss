import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.clients.llm import (
    BankRankingResult,
    BankRecommendationResult,
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
        retrieval_candidates = self._hybrid_retrieval_candidates(candidates, session, limit=10)
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
                for question in retrieval_candidates
            ],
            question_count=INITIAL_QUESTION_BATCH_SIZE,
            target=selection_context,
        )
        retrieval_candidate_ids = {question.id for question in retrieval_candidates}
        selected_id = next(
            (
                item.question_id
                for item in selection.items
                if item.question_id in retrieval_candidate_ids
            ),
            retrieval_candidates[0].id,
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
        rank_reason = next(
            (
                question.retrieval_reason
                for question in _ranked_candidates(candidates, session)
                if question.question.id == selected_id
            ),
            "混合检索候选题。",
        )
        self.interviews.create_item(
            session.id,
            selected_id,
            len(session.items) + 1,
            reason_by_id.get(selected_id, rank_reason),
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
        ranking, plan, selected_bank_ids = self._build_retrieval_plan(
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

    def _build_retrieval_plan(
        self,
        banks: list[QuestionBank],
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
        question_count: int,
    ) -> tuple[BankRankingResult, InterviewPlanResult, list[str]]:
        ranked_banks = _rank_banks_for_retrieval(banks, resume_summary, target)
        selected_bank_ids = [
            bank.bank.id for bank in ranked_banks if bank.bank.question_count > 0
        ][:5]
        bank_candidates = [bank_to_candidate(item.bank) for item in ranked_banks]
        recommendations = [
            BankRecommendationResult(
                bank_id=item.bank.id,
                name=item.bank.name,
                score=item.score,
                reasons=[item.reason],
                matched_keywords=item.matched_keywords,
                question_count=item.bank.question_count,
            )
            for item in ranked_banks
        ]
        ranking = BankRankingResult(
            strategy="混合检索：先按题库描述、岗位、简历技能和题量收敛候选题库。",
            reason="已用检索策略完成题库候选收敛，避免首题阶段多次大模型调用。",
            recommendations=recommendations,
        )
        plan = _build_quota_plan(
            resume_summary=resume_summary,
            target=target,
            flow_mode=flow_mode,
            question_count=question_count,
            selected_banks=bank_candidates[:5],
        )
        return ranking, plan, selected_bank_ids

    def _hybrid_retrieval_candidates(
        self,
        candidates: list[Question],
        session: InterviewSession,
        *,
        limit: int,
    ) -> list[Question]:
        ranked = _ranked_candidates(candidates, session)
        for item in ranked:
            _ensure_question_retrieval_embedding(item.question)
        self.db.flush()
        return [item.question for item in ranked[: max(1, limit)]]

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


@dataclass(frozen=True)
class RankedBank:
    bank: QuestionBank
    score: int
    reason: str
    matched_keywords: list[str]


@dataclass(frozen=True)
class RankedQuestion:
    question: Question
    score: float
    retrieval_reason: str


def _rank_banks_for_retrieval(
    banks: list[QuestionBank],
    resume_summary: dict[str, Any] | None,
    target: str | None,
) -> list[RankedBank]:
    query_terms = set(_retrieval_terms(_resume_query_text(resume_summary, target)))
    query_vector = _embedding_for_text(_resume_query_text(resume_summary, target))
    ranked: list[RankedBank] = []
    for bank in banks:
        bank_text = _bank_retrieval_text(bank)
        bank_terms = set(_retrieval_terms(bank_text))
        matched = sorted(query_terms & bank_terms)
        vector_score = _cosine(query_vector, _embedding_for_text(bank_text))
        keyword_score = min(35, len(matched) * 8)
        volume_score = min(20, bank.question_count * 2)
        score = max(0, min(100, round(vector_score * 45 + keyword_score + volume_score)))
        reasons = []
        if matched:
            reasons.append(f"匹配关键词：{'、'.join(matched[:6])}")
        if bank.question_count:
            reasons.append(f"题量 {bank.question_count}")
        ranked.append(
            RankedBank(
                bank=bank,
                score=score,
                reason="；".join(reasons) or "作为补充候选题库。",
                matched_keywords=matched[:10],
            ),
        )
    ranked.sort(key=lambda item: (-item.score, item.bank.name))
    return ranked


def _build_quota_plan(
    *,
    resume_summary: dict[str, Any] | None,
    target: str | None,
    flow_mode: str,
    question_count: int,
    selected_banks: list[QuestionBankCandidate],
) -> InterviewPlanResult:
    skills = list((resume_summary or {}).get("skills") or [])
    bank_focus = [
        keyword
        for bank in selected_banks
        for keyword in [*bank.skill_keywords, *bank.default_tags, *bank.domains]
    ]
    focus = list(dict.fromkeys([*skills, *bank_focus]))[:8] or ["岗位基础", "项目实践"]
    project_count = 1 if question_count <= 2 else max(1, round(question_count * 0.4))
    general_count = 0 if question_count <= 2 else max(1, round(question_count * 0.3))
    skill_count = max(0, question_count - project_count - general_count)
    if flow_mode == "project_first":
        stages = [
            InterviewStagePlanResult(
                stage="project_deep_dive",
                title="项目深挖",
                objective="围绕简历项目确认真实参与度、关键方案和技术取舍。",
                question_count=project_count,
                focus=focus[:5],
            ),
            InterviewStagePlanResult(
                stage="knowledge_linked",
                title="项目知识点联动",
                objective="从项目相关技术点延伸到知识库题目，确认原理和边界。",
                question_count=skill_count,
                focus=focus[:6],
            ),
            InterviewStagePlanResult(
                stage="general_probe",
                title="岗位通用考察",
                objective="保留岗位高频基础题和八股题配额，避免只围绕简历发问。",
                question_count=general_count,
                focus=[target or "岗位基础", *focus[:4]],
            ),
        ]
    else:
        stages = [
            InterviewStagePlanResult(
                stage="general_probe",
                title="岗位通用考察",
                objective="先通过岗位高频基础题判断知识面和基本功。",
                question_count=general_count,
                focus=[target or "岗位基础", *focus[:4]],
            ),
            InterviewStagePlanResult(
                stage="knowledge_probe",
                title="知识点抽查",
                objective="围绕简历技能和题库标签抽查核心知识点。",
                question_count=skill_count,
                focus=focus[:6],
            ),
            InterviewStagePlanResult(
                stage="project_follow_up",
                title="项目反向追问",
                objective="把知识题落回简历项目，确认实践深度。",
                question_count=project_count,
                focus=focus[:5],
            ),
        ]
    stages = [stage for stage in stages if stage.question_count > 0]
    return InterviewPlanResult(
        flow_mode=flow_mode,
        strategy="按项目、知识点和岗位通用题配额组织混合检索面试。",
        reason="检索阶段先收敛候选池，再由大模型对少量候选做最终选题。",
        stages=stages,
    )


def _ranked_candidates(
    candidates: list[Question],
    session: InterviewSession,
) -> list[RankedQuestion]:
    config = session.config_json or {}
    stages = [
        InterviewStagePlanResult.model_validate(stage)
        for stage in config.get("stage_plan", [])
    ]
    next_position = len(session.items) + 1
    stage = _stage_for_position(stages, next_position)
    query_text = _question_query_text(session, stage)
    query_terms = set(_retrieval_terms(query_text))
    query_vector = _embedding_for_text(query_text)
    answered_tags = [
        tag
        for item in session.items
        if item.status == "answered"
        for tag in item.question.tag_names
    ]
    ranked: list[RankedQuestion] = []
    for question in candidates:
        question_text = _question_retrieval_text(question)
        question_terms = set(_retrieval_terms(question_text))
        matched = sorted(query_terms & question_terms)
        vector_score = _cosine(query_vector, _embedding_for_text(question_text))
        keyword_score = len(matched) * 4
        stage_score = _stage_match_score(question, stage)
        difficulty_score = 10 - abs((question.difficulty_score or 50) - 60) / 10
        diversity_penalty = _diversity_penalty(question.tag_names, answered_tags)
        score = (
            vector_score * 55
            + keyword_score
            + stage_score
            + difficulty_score
            - diversity_penalty
        )
        reason = (
            f"向量相似度 {round(vector_score, 2)}，"
            f"命中 {'、'.join(matched[:5]) or '少量关键词'}，阶段 {_stage_label(stage)}。"
        )
        ranked.append(RankedQuestion(question=question, score=score, retrieval_reason=reason))
    ranked.sort(key=lambda item: (-item.score, item.question.updated_at))
    return ranked


def _stage_for_position(stages: list[InterviewStagePlanResult], position: int) -> str:
    cursor = 0
    for stage in stages:
        cursor += max(0, stage.question_count)
        if position <= cursor:
            return stage.stage
    return stages[-1].stage if stages else "knowledge"


def _question_query_text(session: InterviewSession, stage: str) -> str:
    resume_summary = session.resume.summary_json if session.resume else None
    if stage == "general_probe":
        return f"{session.target or ''} 岗位通用基础 高频八股 常识题"
    answered_context = " ".join(
        item.question.question
        for item in sorted(session.items, key=lambda item: item.position)[-2:]
    )
    return " ".join(
        [
            _resume_query_text(resume_summary, session.target),
            _stage_label(stage),
            answered_context,
        ],
    )


def _resume_query_text(resume_summary: dict[str, Any] | None, target: str | None) -> str:
    parts = [target or ""]
    if not resume_summary:
        return " ".join(parts)
    parts.extend(str(skill) for skill in resume_summary.get("skills") or [])
    parts.extend(str(direction) for direction in resume_summary.get("follow_up_directions") or [])
    for project in resume_summary.get("projects") or []:
        if not isinstance(project, dict):
            continue
        parts.append(str(project.get("name") or ""))
        parts.append(str(project.get("description") or ""))
        parts.extend(str(tech) for tech in project.get("technologies") or [])
    return " ".join(parts)


def _bank_retrieval_text(bank: QuestionBank) -> str:
    return " ".join(
        [
            bank.name,
            bank.description or "",
            *bank.default_tags,
            *bank.target_roles,
            *bank.skill_keywords,
            *bank.domains,
        ],
    )


def _question_retrieval_text(question: Question) -> str:
    bank = question.bank
    return " ".join(
        [
            question.question,
            question.answer or "",
            *question.tag_names,
            _bank_retrieval_text(bank) if bank else "",
        ],
    )


def _retrieval_terms(text: str) -> list[str]:
    return [
        part
        for part in re.split(r"[\s,，。；;：:、/()\[\]{}<>]+", text.lower())
        if len(part) >= 2
    ]


def _embedding_for_text(text: str, *, dimensions: int = 96) -> list[float]:
    vector = [0.0] * dimensions
    terms = _retrieval_terms(text)
    if not terms:
        return vector
    for term in terms:
        digest = hashlib.sha256(term.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=False))


def _stage_match_score(question: Question, stage: str) -> float:
    text = _question_retrieval_text(question)
    if stage in {"project_deep_dive", "project_follow_up"}:
        return 14 if any(word in text for word in ("项目", "实践", "方案", "系统")) else 0
    if stage == "general_probe":
        return 12 if any(word in text for word in ("基础", "原理", "区别", "什么是")) else 4
    return 10 if question.tag_names else 4


def _diversity_penalty(question_tags: list[str], answered_tags: list[str]) -> float:
    if not question_tags or not answered_tags:
        return 0
    overlap = len(set(question_tags) & set(answered_tags))
    return min(12, overlap * 4)


def _ensure_question_retrieval_embedding(question: Question) -> None:
    text = _question_retrieval_text(question)
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if question.retrieval_text_hash == text_hash and question.retrieval_embedding_json:
        return
    question.retrieval_text_hash = text_hash
    question.retrieval_embedding_json = _embedding_for_text(text)


def _stage_label(stage: str) -> str:
    labels = {
        "project_deep_dive": "项目追问",
        "project_follow_up": "项目追问",
        "knowledge_linked": "知识点考察",
        "knowledge_probe": "知识点考察",
        "knowledge": "知识点考察",
        "general_probe": "岗位通用",
    }
    return labels.get(stage, stage)
