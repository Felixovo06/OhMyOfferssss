import math
import re
from collections import Counter
from dataclasses import dataclass
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
RECALL_CANDIDATE_LIMIT = 80
LLM_CANDIDATE_LIMIT = 24


@dataclass(frozen=True)
class QuestionSelectionProfile:
    terms: list[str]
    focus_terms: list[str]
    topic_order: list[str]
    topic_terms: dict[str, set[str]]
    difficulty_min: int | None
    difficulty_max: int | None
    target_difficulty: int
    duration_minutes: int | None


TOPIC_ALIASES: dict[str, set[str]] = {
    "Java基础": {"java", "jvm", "集合", "hashmap", "string", "类加载", "泛型", "异常"},
    "Java并发": {
        "并发",
        "多线程",
        "线程",
        "线程池",
        "aqs",
        "volatile",
        "synchronized",
        "reentrantlock",
        "锁",
        "cas",
    },
    "Redis": {"redis", "缓存", "穿透", "击穿", "雪崩", "热点", "key", "持久化", "rdb", "aof"},
    "MySQL": {"mysql", "sql", "索引", "事务", "隔离级别", "innodb", "b+树", "慢查询", "锁表"},
    "计算机网络": {"网络", "tcp", "http", "https", "三次握手", "四次挥手", "连接", "协议"},
    "操作系统": {"操作系统", "进程", "线程", "内存", "虚拟内存", "io", "上下文切换", "死锁"},
    "设计模式": {"设计模式", "单例", "工厂", "代理", "策略", "观察者", "模板方法"},
    "AI Agent": {"agent", "智能体", "工具调用", "function calling", "规划", "反思", "memory"},
    "RAG": {"rag", "检索", "向量", "embedding", "召回", "重排", "rerank", "知识库"},
}

ROLE_DEFAULT_TOPICS: dict[str, list[str]] = {
    "java-backend": [
        "Java基础",
        "Java并发",
        "Redis",
        "MySQL",
        "计算机网络",
        "操作系统",
        "设计模式",
    ],
    "backend": ["Redis", "MySQL", "计算机网络", "操作系统", "设计模式"],
    "ai-application": ["AI Agent", "RAG", "Redis", "MySQL"],
}


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
        if mode == "normal":
            self._prepare_initial_items(user, session, payload)
            if not session.items:
                self.db.rollback()
                raise AppError(
                    "NOT_ENOUGH_QUESTIONS",
                    "符合条件的候选题不足",
                    status_code=422,
                    details={"required": 1, "available": 0},
                )
            session.strategy = "已按本地硬过滤、混合召回、去重重排和 LLM/规则编排生成普通面试题。"
        self.db.commit()
        return self.get_session(user, session.id)

    def _prepare_initial_items(
        self,
        user: User,
        session: InterviewSession,
        payload: InterviewCreate,
    ) -> None:
        self._ensure_session_plan(user, session, payload)
        payload = InterviewCreate.model_validate(session.config_json or {})
        candidates = self._candidate_questions(user, payload, payload.bank_ids)
        candidates = self._rank_candidate_questions(
            candidates,
            payload,
            session,
            limit=_llm_candidate_limit(payload.question_count),
        )
        if not candidates:
            return

        selection_context = self._selection_context(session)
        candidate_limit = _llm_candidate_limit(payload.question_count)
        llm_candidates = candidates[:candidate_limit]
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
                for question in llm_candidates
            ],
            question_count=payload.question_count,
            target=selection_context,
        )
        valid_ids = {question.id for question in llm_candidates}
        selected_ids = [
            item.question_id
            for item in selection.items
            if item.question_id in valid_ids
        ]
        selected_ids = list(dict.fromkeys(selected_ids))
        for question in llm_candidates:
            if len(selected_ids) >= payload.question_count:
                break
            if question.id not in selected_ids:
                selected_ids.append(question.id)

        selected_ids = selected_ids[: payload.question_count]
        plan_stages = [
            InterviewStagePlanResult.model_validate(stage)
            for stage in (session.config_json or {}).get("stage_plan", [])
        ]
        metadata_by_id = self._item_stage_metadata(
            plan_stages,
            selected_ids,
            candidates,
            session.resume.summary_json if session.resume else None,
        )
        reason_by_id = {item.question_id: item.reason for item in selection.items}
        for index, question_id in enumerate(selected_ids, start=1):
            metadata = metadata_by_id.get(question_id, {})
            item = self.interviews.create_item(
                session.id,
                question_id,
                index,
                reason_by_id.get(question_id, "按本轮候选题综合排序选入。"),
                stage=metadata.get("stage") or "knowledge",
                intent=metadata.get("intent") or "知识点考察",
                related_project=metadata.get("related_project"),
                related_skill=metadata.get("related_skill"),
            )
            if item not in session.items:
                session.items.append(item)
        session.selection_reason = selection.reason

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
        candidates = self._rank_candidate_questions(candidates, payload, session)
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
                for question in candidates[:LLM_CANDIDATE_LIMIT]
            ],
            question_count=INITIAL_QUESTION_BATCH_SIZE,
            target=selection_context,
        )
        candidate_ids = {question.id for question in candidates[:LLM_CANDIDATE_LIMIT]}
        selected_id = next(
            (
                item.question_id
                for item in selection.items
                if item.question_id in candidate_ids
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
            position_offset=len(session.items),
        ).get(selected_id, {})
        reason_by_id = {item.question_id: item.reason for item in selection.items}
        item = self.interviews.create_item(
            session.id,
            selected_id,
            len(session.items) + 1,
            reason_by_id.get(selected_id, "按需补充下一题。"),
            stage=metadata.get("stage") or "knowledge",
            intent=metadata.get("intent") or "知识点考察",
            related_project=metadata.get("related_project"),
            related_skill=metadata.get("related_skill"),
        )
        if item not in session.items:
            session.items.append(item)
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
        difficulty_min, difficulty_max = _difficulty_bounds(payload)
        for bank_id in bank_ids:
            self.banks.get_accessible_bank(user, bank_id)
            questions = self.questions.list_questions(user, bank_id, enabled=True)
            for question in questions:
                if question.id in seen:
                    continue
                if (
                    difficulty_min is not None
                    and question.difficulty_score is not None
                    and question.difficulty_score < difficulty_min
                ):
                    continue
                if (
                    difficulty_max is not None
                    and question.difficulty_score is not None
                    and question.difficulty_score > difficulty_max
                ):
                    continue
                if (
                    (difficulty_min is not None or difficulty_max is not None)
                    and question.difficulty_score is None
                ):
                    continue
                if tags and not tags.intersection(question.tag_names):
                    continue
                seen.add(question.id)
                candidates.append(question)
        return candidates

    def _rank_candidate_questions(
        self,
        candidates: list[Question],
        payload: InterviewCreate,
        session: InterviewSession,
        *,
        limit: int = LLM_CANDIDATE_LIMIT,
    ) -> list[Question]:
        if not candidates:
            return []

        resume_summary = session.resume.summary_json if session.resume else None
        profile = _selection_profile(payload, session.target, resume_summary)
        scoped = _hard_filter_by_topic(candidates, profile)
        scored = _score_candidates(scoped, profile, session.items)
        recalled = [question for question, _score in scored[:RECALL_CANDIDATE_LIMIT]]
        return _dedupe_and_balance_questions(
            recalled,
            profile,
            limit=min(len(recalled), limit),
            existing_items=session.items,
        )

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
        *,
        position_offset: int = 0,
    ) -> dict[str, dict[str, str | None]]:
        candidate_by_id = {question.id: question for question in candidates}
        projects = [
            str(project.get("name") or project.get("description"))
            for project in list((resume_summary or {}).get("projects") or [])
            if isinstance(project, dict) and (project.get("name") or project.get("description"))
        ]
        metadata: dict[str, dict[str, str | None]] = {}
        for index, question_id in enumerate(selected_ids):
            absolute_position = position_offset + index
            cursor = 0
            matched_stage: InterviewStagePlanResult | None = None
            for stage in stages:
                count = max(0, stage.question_count)
                if cursor <= absolute_position < cursor + count:
                    matched_stage = stage
                    break
                cursor += count
            if matched_stage:
                question = candidate_by_id.get(question_id)
                related_skill = None
                if question:
                    related_skill = next(iter(question.tag_names), None)
                metadata[question_id] = {
                    "stage": matched_stage.stage,
                    "intent": matched_stage.objective[:120],
                    "related_project": projects[0][:200] if projects else None,
                    "related_skill": related_skill,
                }
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


def _selection_profile(
    payload: InterviewCreate,
    target: str | None,
    resume_summary: dict[str, Any] | None,
) -> QuestionSelectionProfile:
    text_parts = [target or "", payload.goal or "", *payload.tags]
    if resume_summary:
        text_parts.extend(str(skill) for skill in resume_summary.get("skills") or [])
        text_parts.extend(
            str(direction) for direction in resume_summary.get("follow_up_directions") or []
        )
        for project in resume_summary.get("projects") or []:
            if not isinstance(project, dict):
                continue
            text_parts.append(str(project.get("name") or ""))
            text_parts.append(str(project.get("description") or ""))
            text_parts.extend(str(tech) for tech in project.get("technologies") or [])

    text = " ".join(text_parts).lower()
    topic_order: list[str] = []
    if "java" in text and "后端" in text:
        topic_order.extend(ROLE_DEFAULT_TOPICS["java-backend"])
    elif "后端" in text:
        topic_order.extend(ROLE_DEFAULT_TOPICS["backend"])
    if "ai" in text or "agent" in text or "rag" in text or "智能体" in text:
        topic_order.extend(ROLE_DEFAULT_TOPICS["ai-application"])

    for topic, aliases in TOPIC_ALIASES.items():
        if topic.lower() in text or any(alias in text for alias in aliases):
            topic_order.append(topic)
    topic_order = list(dict.fromkeys(topic_order))

    focus_terms = _text_terms(text)
    for topic in topic_order:
        focus_terms.extend(TOPIC_ALIASES.get(topic, set()))
    focus_terms = list(dict.fromkeys(term for term in focus_terms if term))

    difficulty_min, difficulty_max = _difficulty_bounds(payload)
    inferred_min, inferred_max = _difficulty_bounds_from_text(text)
    difficulty_min = difficulty_min if difficulty_min is not None else inferred_min
    difficulty_max = difficulty_max if difficulty_max is not None else inferred_max
    if difficulty_min is None and difficulty_max is None:
        target_difficulty = 60 if ("3年" in text or "三年" in text or "中级" in text) else 50
    else:
        lower = difficulty_min if difficulty_min is not None else 0
        upper = difficulty_max if difficulty_max is not None else 100
        target_difficulty = round((lower + upper) / 2)

    return QuestionSelectionProfile(
        terms=focus_terms[:80],
        focus_terms=focus_terms[:80],
        topic_order=topic_order,
        topic_terms={topic: set(TOPIC_ALIASES[topic]) for topic in topic_order},
        difficulty_min=difficulty_min,
        difficulty_max=difficulty_max,
        target_difficulty=target_difficulty,
        duration_minutes=_duration_from_text(text) or payload.duration_minutes,
    )


def _difficulty_bounds(payload: InterviewCreate) -> tuple[int | None, int | None]:
    difficulty_min = payload.difficulty_min
    difficulty_max = payload.difficulty_max
    if payload.difficulty is not None and difficulty_max is None:
        difficulty_max = payload.difficulty * 20 if payload.difficulty <= 5 else payload.difficulty
    return difficulty_min, difficulty_max


def _difficulty_bounds_from_text(text: str) -> tuple[int | None, int | None]:
    if "初级" in text:
        return 0, 45
    if "中级" in text or "3年" in text or "三年" in text:
        return 31, 80
    if "高级" in text or "架构" in text or "资深" in text:
        return 61, 100
    return None, None


def _duration_from_text(text: str) -> int | None:
    match = re.search(r"(\d{1,3})\s*(?:min|分钟)", text, flags=re.I)
    if not match:
        return None
    return int(match.group(1))


def _hard_filter_by_topic(
    candidates: list[Question],
    profile: QuestionSelectionProfile,
) -> list[Question]:
    if not profile.topic_order and not profile.focus_terms:
        return candidates
    scoped = [
        question
        for question in candidates
        if _primary_topic(question, profile) is not None
        or _contains_any(_question_search_text(question), profile.focus_terms)
    ]
    return scoped or candidates


def _score_candidates(
    candidates: list[Question],
    profile: QuestionSelectionProfile,
    existing_items: list[InterviewItem],
) -> list[tuple[Question, float]]:
    terms = profile.terms
    document_frequency: Counter[str] = Counter()
    search_text_by_id = {question.id: _question_search_text(question) for question in candidates}
    for text in search_text_by_id.values():
        for term in terms:
            if term and term in text:
                document_frequency[term] += 1

    max_keyword_score = 0.0
    raw_keyword_scores: dict[str, float] = {}
    total_count = max(len(candidates), 1)
    for question in candidates:
        score = 0.0
        text = search_text_by_id[question.id]
        for term in terms:
            if term and term in text:
                score += math.log((total_count + 1) / (document_frequency[term] + 1)) + 1
        raw_keyword_scores[question.id] = score
        max_keyword_score = max(max_keyword_score, score)

    last_topic = _primary_topic(existing_items[-1].question, profile) if existing_items else None
    scored: list[tuple[Question, float]] = []
    for question in candidates:
        text = search_text_by_id[question.id]
        topic = _primary_topic(question, profile)
        topic_hits = sum(
            1 for aliases in profile.topic_terms.values() if _contains_any(text, aliases)
        )
        vector_score = (
            min(1.0, topic_hits / max(len(profile.topic_terms), 1))
            if profile.topic_terms
            else 0
        )
        keyword_score = raw_keyword_scores[question.id] / max(max_keyword_score, 1)
        tag_score = _tag_score(question, profile)
        quality_score = _quality_score(question, profile)
        continuity_penalty = 0.08 if topic and topic == last_topic else 0
        score = (
            0.45 * vector_score
            + 0.35 * keyword_score
            + 0.15 * tag_score
            + 0.05 * quality_score
            - continuity_penalty
        )
        scored.append((question, score))
    scored.sort(
        key=lambda item: (
            -item[1],
            abs(
                (item[0].difficulty_score or profile.target_difficulty)
                - profile.target_difficulty,
            ),
            item[0].question,
        ),
    )
    return scored


def _dedupe_and_balance_questions(
    ranked_questions: list[Question],
    profile: QuestionSelectionProfile,
    *,
    limit: int,
    existing_items: list[InterviewItem],
) -> list[Question]:
    deduped: list[Question] = []
    seen_keys: set[str] = set()
    seen_term_sets: list[set[str]] = []
    for question in ranked_questions:
        key = _normalized_question_key(question.question)
        term_set = set(_text_terms(question.question))
        if key in seen_keys:
            continue
        if any(_jaccard(term_set, seen) >= 0.82 for seen in seen_term_sets):
            continue
        seen_keys.add(key)
        seen_term_sets.append(term_set)
        deduped.append(question)

    if not profile.topic_order:
        return deduped[:limit]

    quotas = _topic_quotas(profile, limit)
    selected: list[Question] = []
    topic_counts: Counter[str] = Counter()
    last_topic = _primary_topic(existing_items[-1].question, profile) if existing_items else None
    for question in deduped:
        topic = _primary_topic(question, profile) or "通用"
        if len(selected) >= limit:
            break
        if topic == last_topic and len(selected) < len(deduped) - 1:
            continue
        if topic_counts[topic] >= quotas.get(topic, limit):
            continue
        selected.append(question)
        topic_counts[topic] += 1
        last_topic = topic

    if len(selected) < limit:
        selected_ids = {question.id for question in selected}
        for question in deduped:
            if question.id in selected_ids:
                continue
            selected.append(question)
            if len(selected) >= limit:
                break
    return selected


def _topic_quotas(profile: QuestionSelectionProfile, limit: int) -> dict[str, int]:
    if not profile.topic_order:
        return {}
    weights = {topic: 1 for topic in profile.topic_order}
    focus_text = " ".join(profile.focus_terms)
    for topic, aliases in profile.topic_terms.items():
        if topic.lower() in focus_text or any(alias in focus_text for alias in aliases):
            weights[topic] += 1
    total_weight = max(sum(weights.values()), 1)
    quotas = {
        topic: max(1, round(limit * weight / total_weight))
        for topic, weight in weights.items()
    }
    while sum(quotas.values()) < limit:
        quotas[profile.topic_order[0]] += 1
    return quotas


def _primary_topic(question: Question, profile: QuestionSelectionProfile) -> str | None:
    text = _question_search_text(question)
    tag_text = " ".join(tag.lower() for tag in question.tag_names)
    for topic in [*profile.topic_order, *TOPIC_ALIASES.keys()]:
        aliases = TOPIC_ALIASES[topic]
        if topic.lower() in tag_text or any(alias in tag_text for alias in aliases):
            return topic
        if _contains_any(text, aliases):
            return topic
    return None


def _tag_score(question: Question, profile: QuestionSelectionProfile) -> float:
    if not profile.focus_terms and not profile.topic_order:
        return 0.5
    tags = {tag.lower() for tag in question.tag_names}
    if not tags:
        return 0
    hits = 0
    for tag in tags:
        if tag in profile.focus_terms or any(
            term in tag or tag in term for term in profile.focus_terms
        ):
            hits += 1
    return min(1.0, hits / max(len(tags), 1))


def _quality_score(question: Question, profile: QuestionSelectionProfile) -> float:
    answer_bonus = 0.4 if question.answer else 0
    difficulty = question.difficulty_score
    difficulty_bonus = (
        0.4
        if difficulty is not None
        else 0.1
    )
    if difficulty is not None:
        difficulty_bonus *= max(0.2, 1 - abs(difficulty - profile.target_difficulty) / 100)
    source_bonus = (
        0.2 if question.source_type in {"manual", "feishu_import", "github_import"} else 0.1
    )
    return min(1.0, answer_bonus + difficulty_bonus + source_bonus)


def _question_search_text(question: Question) -> str:
    return " ".join(
        [
            question.question,
            question.answer or "",
            " ".join(question.tag_names),
            question.difficulty_label or "",
        ],
    ).lower()


def _contains_any(text: str, terms: set[str] | list[str]) -> bool:
    return any(term and term.lower() in text for term in terms)


def _text_terms(text: str) -> list[str]:
    normalized = re.sub(r"[，。、“”‘’：:；;,.!?？()\[\]{}<>/\\|+*=~`\"']", " ", text.lower())
    terms = [part.strip() for part in normalized.split() if part.strip()]
    for token in ("java", "redis", "mysql", "rag", "agent", "aqs", "volatile", "tcp", "http"):
        if token in text.lower():
            terms.append(token)
    for token in ("后端", "并发", "缓存", "索引", "事务", "线程池", "持久化", "高并发", "热点"):
        if token in text:
            terms.append(token)
    return list(dict.fromkeys(terms))


def _normalized_question_key(question: str) -> str:
    return re.sub(r"\s+", "", question.lower().strip(" ?？。,.，"))


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0
    return len(left & right) / len(left | right)


def _llm_candidate_limit(question_count: int) -> int:
    return min(RECALL_CANDIDATE_LIMIT, max(LLM_CANDIDATE_LIMIT, question_count * 2))


def _stage_label(stage: str) -> str:
    labels = {
        "project_deep_dive": "项目追问",
        "project_follow_up": "项目追问",
        "knowledge_linked": "知识点考察",
        "knowledge_probe": "知识点考察",
        "knowledge": "知识点考察",
    }
    return labels.get(stage, stage)
