import json
import logging
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger("app.clients.llm")


class ExtractedQuestion(BaseModel):
    question: str
    answer: str | None = None
    tags: list[str] = Field(default_factory=list)
    difficulty_score: int = 50
    difficulty_label: str = "medium"
    source_block_ids: list[str] = Field(default_factory=list)
    confidence: float = 0.8
    notes: str | None = None


class ExtractedQuestionList(BaseModel):
    items: list[ExtractedQuestion]


class InterviewCandidate(BaseModel):
    id: str
    question: str
    answer: str | None = None
    tags: list[str] = Field(default_factory=list)
    difficulty_score: int = 50
    difficulty_label: str = "medium"


class QuestionBankCandidate(BaseModel):
    id: str
    name: str
    description: str | None = None
    default_tags: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)
    skill_keywords: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    question_count: int = 0


class BankRecommendationResult(BaseModel):
    bank_id: str
    name: str = ""
    score: int = Field(default=0, ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    question_count: int = 0

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "bank_id" not in normalized:
            normalized["bank_id"] = normalized.get("id") or normalized.get("question_bank_id")
        score = normalized.get("score", 0)
        if isinstance(score, float) and 0 <= score <= 1:
            normalized["score"] = round(score * 100)
        if isinstance(score, str):
            try:
                parsed_score = float(score.rstrip("%"))
                normalized["score"] = (
                    round(parsed_score * 100) if 0 <= parsed_score <= 1 else round(parsed_score)
                )
            except ValueError:
                normalized["score"] = 0
        reasons = normalized.get("reasons")
        if isinstance(reasons, str):
            normalized["reasons"] = [reasons]
        matched = normalized.get("matched_keywords") or normalized.get("keywords")
        if isinstance(matched, str):
            normalized["matched_keywords"] = [matched]
        elif matched is not None:
            normalized["matched_keywords"] = matched
        return normalized


class BankRankingResult(BaseModel):
    strategy: str
    reason: str
    recommendations: list[BankRecommendationResult]

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        if "recommendations" not in normalized:
            normalized["recommendations"] = (
                normalized.get("recommended_banks")
                or normalized.get("banks")
                or normalized.get("items")
                or []
            )
        normalized.setdefault("strategy", "大模型根据简历、岗位和题库语义匹配题库。")
        normalized.setdefault("reason", "大模型返回了题库推荐结果。")
        return normalized


class InterviewSelectionItem(BaseModel):
    question_id: str
    reason: str


class InterviewSelection(BaseModel):
    strategy: str
    reason: str
    items: list[InterviewSelectionItem]


class InterviewStagePlanResult(BaseModel):
    stage: str
    title: str
    objective: str
    question_count: int
    focus: list[str] = Field(default_factory=list)


class InterviewPlanResult(BaseModel):
    flow_mode: str
    strategy: str
    reason: str
    stages: list[InterviewStagePlanResult]


class InterviewFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_points: list[str] = Field(default_factory=list)
    reference_answer: str
    follow_up: str | None = None
    comment: str
    next_action: str = "next_question"
    next_stage: str | None = None
    decision_reason: str | None = None

    @field_validator("next_action")
    @classmethod
    def normalize_next_action(cls, value: str) -> str:
        normalized = value.strip().lower()
        mapping = {
            "continue": "continue_project",
            "follow_up": "continue_project",
            "project": "continue_project",
            "knowledge": "switch_knowledge",
            "switch": "switch_knowledge",
            "next": "next_question",
            "next_question": "next_question",
            "summary": "summary",
        }
        return mapping.get(normalized, normalized)


class ProjectPerformanceResult(BaseModel):
    project_name: str
    score: int = Field(ge=0, le=100)
    comment: str


class KnowledgePerformanceResult(BaseModel):
    tag: str
    mastery: float = Field(ge=0, le=1)


class ReviewPlanItemResult(BaseModel):
    topic: str
    suggestion: str


class InterviewSummaryResult(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    project_performance: list[ProjectPerformanceResult] = Field(default_factory=list)
    knowledge_performance: list[KnowledgePerformanceResult] = Field(default_factory=list)
    review_plan: list[ReviewPlanItemResult] = Field(default_factory=list)
    comment: str


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_questions_from_text(self, normalized_text: str) -> ExtractedQuestionList:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_extract(normalized_text)

        extracted_items: list[ExtractedQuestion] = []
        for chunk in _split_text_chunks(normalized_text):
            payload = self._chat_json(
                [
                    {
                        "role": "system",
                        "content": (
                            "你是面试题库导入助手。请逐行扫描资料，穷尽抽取面试题，"
                            "不要只总结重点，不要省略尾部内容。规则："
                            "1. 每个明确问题、知识点标题、小节标题都尽量生成独立题目；"
                            "2. 标题不是问句时，改写成自然的面试问句；"
                            "3. 答案必须尽量保留原文细节和列表项，不要过度压缩；"
                            "4. 不要把不同知识点合并成一道题；"
                            "5. source_block_ids 填相关原文 block id。"
                            "严格返回 JSON：{\"items\": [{\"question\": string, "
                            "\"answer\": string|null, \"tags\": string[], "
                            "\"difficulty_score\": number, \"difficulty_label\": string, "
                            "\"source_block_ids\": string[], \"confidence\": number, "
                            "\"notes\": string|null}]}"
                        ),
                    },
                    {"role": "user", "content": chunk},
                ],
                thinking=False,
            )
            try:
                extracted_items.extend(ExtractedQuestionList.model_validate(payload).items)
            except ValidationError as exc:
                raise AppError(
                    "LLM_INVALID_RESPONSE",
                    "大模型抽题响应格式无效",
                    status_code=502,
                ) from exc

        return ExtractedQuestionList(items=_dedupe_questions(extracted_items))

    def select_interview_questions(
        self,
        candidates: list[InterviewCandidate],
        *,
        question_count: int,
        target: str | None,
    ) -> InterviewSelection:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_select(candidates, question_count=question_count, target=target)

        payload = self._chat_tool_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试官。请从候选题中选择普通面试题，必须调用 "
                        "return_interview_selection 工具返回结果。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "target": target,
                            "question_count": question_count,
                            "candidates": [candidate.model_dump() for candidate in candidates],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            tool_name="return_interview_selection",
            description="Return selected interview questions.",
            parameters=interview_selection_tool_schema(),
        )
        try:
            return _validate_llm_response(
                InterviewSelection,
                payload,
                "大模型选题响应格式无效",
            )
        except AppError as exc:
            if exc.code != "LLM_INVALID_RESPONSE":
                raise
            logger.warning("llm_selection_invalid_response fallback=rule_based")
            return self._rule_based_select(candidates, question_count=question_count, target=target)

    def rank_question_banks(
        self,
        banks: list[QuestionBankCandidate],
        *,
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
    ) -> BankRankingResult:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_rank_banks(
                banks,
                resume_summary=resume_summary,
                target=target,
                flow_mode=flow_mode,
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是面试题库匹配助手。请根据候选人简历、岗位目标和题库语义信息，"
                    "选择最相关的题库。必须调用 return_bank_ranking 工具返回结果。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "target": target,
                        "flow_mode": flow_mode,
                        "resume_summary": resume_summary,
                        "banks": [bank.model_dump() for bank in banks],
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        payload = self._chat_tool_json(
            messages,
            tool_name="return_bank_ranking",
            description="Return ranked interview question banks.",
            parameters=bank_ranking_tool_schema(),
        )
        try:
            return _validate_llm_response(
                BankRankingResult,
                payload,
                "大模型题库匹配响应格式无效",
            )
        except AppError as exc:
            if exc.code != "LLM_INVALID_RESPONSE":
                raise
            logger.warning("llm_bank_ranking_invalid_response fallback=rule_based")
            return self._rule_based_rank_banks(
                banks,
                resume_summary=resume_summary,
                target=target,
                flow_mode=flow_mode,
            )

    def plan_interview_flow(
        self,
        *,
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
        question_count: int,
        selected_banks: list[QuestionBankCandidate],
    ) -> InterviewPlanResult:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_plan_flow(
                resume_summary=resume_summary,
                target=target,
                flow_mode=flow_mode,
                question_count=question_count,
                selected_banks=selected_banks,
            )

        payload = self._chat_tool_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是资深技术面试官。请规划一轮项目面试和知识库联动面试，"
                        "不要编造简历不存在的项目经历。必须调用 return_interview_plan "
                        "工具返回结果。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "target": target,
                            "flow_mode": flow_mode,
                            "question_count": question_count,
                            "resume_summary": resume_summary,
                            "selected_banks": [bank.model_dump() for bank in selected_banks],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            tool_name="return_interview_plan",
            description="Return the interview flow plan.",
            parameters=interview_plan_tool_schema(),
        )
        try:
            return _validate_llm_response(
                InterviewPlanResult,
                payload,
                "大模型面试规划响应格式无效",
            )
        except AppError as exc:
            if exc.code != "LLM_INVALID_RESPONSE":
                raise
            logger.warning("llm_plan_invalid_response fallback=rule_based")
            return self._rule_based_plan_flow(
                resume_summary=resume_summary,
                target=target,
                flow_mode=flow_mode,
                question_count=question_count,
                selected_banks=selected_banks,
            )

    def score_interview_answer(
        self,
        *,
        question: str,
        reference_answer: str | None,
        user_answer: str,
        target: str | None,
    ) -> InterviewFeedback:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_feedback(
                question=question,
                reference_answer=reference_answer,
                user_answer=user_answer,
            )

        payload = self._chat_tool_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试反馈助手。请评分并给出缺失点、参考表达和追问，"
                        "必须调用 return_interview_feedback 工具返回结果。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "target": target,
                            "question": question,
                            "reference_answer": reference_answer,
                            "user_answer": user_answer,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            tool_name="return_interview_feedback",
            description="Return interview answer feedback.",
            parameters=interview_feedback_tool_schema(),
        )
        try:
            return _validate_llm_response(
                InterviewFeedback,
                payload,
                "大模型评分响应格式无效",
            )
        except AppError as exc:
            if exc.code != "LLM_INVALID_RESPONSE":
                raise
            logger.warning("llm_feedback_invalid_response fallback=rule_based")
            return self._rule_based_feedback(
                question=question,
                reference_answer=reference_answer,
                user_answer=user_answer,
            )

    def summarize_interview(
        self,
        *,
        target: str | None,
        answered_items: list[dict[str, Any]],
    ) -> InterviewSummaryResult:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_summary(target=target, answered_items=answered_items)

        payload = self._chat_tool_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试总结助手。请总结整体表现，必须调用 "
                        "return_interview_summary 工具返回结果。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {"target": target, "answered_items": answered_items},
                        ensure_ascii=False,
                    ),
                },
            ],
            tool_name="return_interview_summary",
            description="Return interview summary.",
            parameters=interview_summary_tool_schema(),
        )
        try:
            return _validate_llm_response(
                InterviewSummaryResult,
                payload,
                "大模型总结响应格式无效",
            )
        except AppError as exc:
            if exc.code != "LLM_INVALID_RESPONSE":
                raise
            logger.warning("llm_summary_invalid_response fallback=rule_based")
            return self._rule_based_summary(target=target, answered_items=answered_items)

    def _chat_json(
        self,
        messages: list[dict[str, str]],
        *,
        thinking: bool | None = None,
    ) -> dict[str, Any]:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            raise AppError("LLM_NOT_CONFIGURED", "大模型服务未配置", status_code=503)

        request_payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "response_format": {"type": "json_object"},
        }
        use_thinking = bool(thinking) and self.settings.llm_thinking_enabled
        if use_thinking:
            request_payload["thinking"] = {"enabled": True}

        try:
            response = httpx.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=60,
                trust_env=False,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            parsed = _parse_json_object(str(content))
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning("llm_http_error status_code=%s", status_code)
            raise AppError("LLM_REQUEST_FAILED", "大模型服务请求失败", status_code=502) from exc
        except (
            httpx.HTTPError,
            ImportError,
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning("llm_invalid_response error=%s", exc.__class__.__name__)
            raise AppError("LLM_INVALID_RESPONSE", "大模型响应无法解析", status_code=502) from exc

        return parsed

    def _chat_tool_json(
        self,
        messages: list[dict[str, str]],
        *,
        tool_name: str,
        description: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            raise AppError("LLM_NOT_CONFIGURED", "大模型服务未配置", status_code=503)

        request_payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": description,
                        "strict": True,
                        "parameters": parameters,
                    },
                },
            ],
        }

        try:
            response = httpx.post(
                f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=60,
                trust_env=False,
            )
            response.raise_for_status()
            payload = response.json()
            message = payload["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []
            if tool_calls:
                arguments = tool_calls[0]["function"]["arguments"]
                parsed = json.loads(str(arguments))
            else:
                parsed = _parse_json_object(str(message.get("content") or ""))
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            logger.warning("llm_tool_http_error status_code=%s", status_code)
            raise AppError("LLM_REQUEST_FAILED", "大模型服务请求失败", status_code=502) from exc
        except (
            httpx.HTTPError,
            ImportError,
            KeyError,
            IndexError,
            TypeError,
            json.JSONDecodeError,
        ) as exc:
            logger.warning("llm_tool_invalid_response error=%s", exc.__class__.__name__)
            raise AppError(
                "LLM_INVALID_RESPONSE",
                "大模型工具响应无法解析",
                status_code=502,
            ) from exc

        if not isinstance(parsed, dict):
            raise AppError("LLM_INVALID_RESPONSE", "大模型工具响应格式无效", status_code=502)
        return parsed

    def _rule_based_extract(self, normalized_text: str) -> ExtractedQuestionList:
        items: list[ExtractedQuestion] = []
        current_question: str | None = None
        current_answer: list[str] = []
        source_blocks: list[str] = []
        for line in normalized_text.splitlines():
            stripped = line.strip()
            block_id = _extract_block_id(stripped)
            if block_id:
                source_blocks.append(block_id)
            if stripped.lower().startswith("q:") or stripped.startswith("问："):
                if current_question:
                    items.append(
                        _build_item(current_question, "\n".join(current_answer), source_blocks),
                    )
                current_question = stripped.split(":", 1)[-1].replace("问：", "").strip()
                current_answer = []
                source_blocks = [block_id] if block_id else []
            elif stripped.lower().startswith("a:") or stripped.startswith("答："):
                current_answer.append(stripped.split(":", 1)[-1].replace("答：", "").strip())
            elif current_question and stripped:
                current_answer.append(stripped)
        if current_question:
            items.append(_build_item(current_question, "\n".join(current_answer), source_blocks))
        if not items and normalized_text.strip():
            items.append(_build_item(normalized_text.strip().splitlines()[0], "", source_blocks))
        return ExtractedQuestionList(items=items)

    def _rule_based_select(
        self,
        candidates: list[InterviewCandidate],
        *,
        question_count: int,
        target: str | None,
    ) -> InterviewSelection:
        sorted_candidates = sorted(
            candidates,
            key=lambda candidate: (
                abs(candidate.difficulty_score - 50),
                candidate.question,
            ),
        )
        selected = sorted_candidates[:question_count]
        target_text = f"，目标是{target}" if target else ""
        return InterviewSelection(
            strategy=f"优先选择启用题中难度居中、覆盖标签较广的题目{target_text}。",
            reason="当前使用规则兜底抽题，保证面试能在无大模型配置时继续进行。",
            items=[
                InterviewSelectionItem(
                    question_id=candidate.id,
                    reason=(
                        f"难度 {candidate.difficulty_score}，标签覆盖 "
                        f"{'、'.join(candidate.tags) if candidate.tags else '通用能力'}。"
                    ),
                )
                for candidate in selected
            ],
        )

    def _rule_based_rank_banks(
        self,
        banks: list[QuestionBankCandidate],
        *,
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
    ) -> BankRankingResult:
        profile_terms = set(_profile_terms(resume_summary, target))
        recommendations: list[BankRecommendationResult] = []
        for bank in banks:
            bank_terms = _keywords(
                " ".join(
                    [
                        bank.name,
                        bank.description or "",
                        *bank.default_tags,
                        *bank.target_roles,
                        *bank.skill_keywords,
                        *bank.domains,
                    ],
                ),
            )
            matched = sorted(profile_terms & set(bank_terms))
            base_score = min(40, bank.question_count * 4)
            semantic_score = min(60, len(matched) * 15)
            score = max(10 if bank.question_count else 0, min(100, base_score + semantic_score))
            reasons = []
            if matched:
                reasons.append(f"匹配简历/岗位关键词：{'、'.join(matched[:6])}")
            if bank.question_count:
                reasons.append(f"题库内有 {bank.question_count} 道候选题")
            if not reasons:
                reasons.append("暂无明显语义匹配，作为补充题库候选")
            recommendations.append(
                BankRecommendationResult(
                    bank_id=bank.id,
                    name=bank.name,
                    score=score,
                    reasons=reasons,
                    matched_keywords=matched[:12],
                    question_count=bank.question_count,
                ),
            )
        recommendations.sort(key=lambda item: (-item.score, item.name))
        target_text = f"，岗位目标为{target}" if target else ""
        return BankRankingResult(
            strategy=f"根据简历技能、项目关键词、题库描述和题量进行规则兜底匹配{target_text}。",
            reason=(
                "当前使用规则兜底题库匹配，后续可由大模型根据题库语义描述给出更细的选择理由。"
                f"流程模式：{flow_mode}。"
            ),
            recommendations=recommendations,
        )

    def _rule_based_plan_flow(
        self,
        *,
        resume_summary: dict[str, Any] | None,
        target: str | None,
        flow_mode: str,
        question_count: int,
        selected_banks: list[QuestionBankCandidate],
    ) -> InterviewPlanResult:
        skills = list((resume_summary or {}).get("skills") or [])
        projects = [
            project.get("name") or project.get("description") or "简历项目"
            for project in list((resume_summary or {}).get("projects") or [])[:2]
            if isinstance(project, dict)
        ]
        bank_focus = [
            keyword
            for bank in selected_banks
            for keyword in [*bank.skill_keywords, *bank.default_tags, *bank.domains]
        ]
        focus = list(dict.fromkeys([*skills, *projects, *bank_focus]))[:8]
        first_count = 1 if question_count <= 2 else max(1, question_count // 3)
        second_count = max(0, question_count - first_count)
        if flow_mode == "project_first":
            stages = [
                InterviewStagePlanResult(
                    stage="project_deep_dive",
                    title="项目深挖",
                    objective="先围绕简历项目确认候选人的真实参与度、技术选型和关键取舍。",
                    question_count=first_count,
                    focus=focus[:5] or ["项目背景", "负责范围", "技术选型"],
                ),
                InterviewStagePlanResult(
                    stage="knowledge_linked",
                    title="项目知识点联动",
                    objective="根据项目中出现的技术点，从相关题库抽取知识题继续追问。",
                    question_count=second_count,
                    focus=focus[:6] or ["相关题库知识点"],
                ),
            ]
        else:
            stages = [
                InterviewStagePlanResult(
                    stage="knowledge_probe",
                    title="知识点抽查",
                    objective="先抽取岗位和简历相关的知识库题，快速判断基础掌握情况。",
                    question_count=second_count,
                    focus=focus[:6] or ["岗位相关知识点"],
                ),
                InterviewStagePlanResult(
                    stage="project_follow_up",
                    title="项目反向追问",
                    objective="根据知识题回答，把问题落回简历项目，确认实践经验和边界理解。",
                    question_count=first_count,
                    focus=focus[:5] or ["项目实践", "故障处理", "性能优化"],
                ),
            ]
        target_text = f"面向{target}，" if target else ""
        flow_label = "项目优先" if flow_mode == "project_first" else "知识优先"
        return InterviewPlanResult(
            flow_mode=flow_mode,
            strategy=f"{target_text}按“{flow_label}”组织面试阶段。",
            reason="当前使用规则兜底生成阶段计划，保证无大模型配置时仍可创建智能面试。",
            stages=stages,
        )

    def _rule_based_feedback(
        self,
        *,
        question: str,
        reference_answer: str | None,
        user_answer: str,
    ) -> InterviewFeedback:
        reference = reference_answer or "建议围绕核心概念、适用场景、关键步骤和常见风险作答。"
        answer_terms = set(_keywords(user_answer))
        reference_terms = set(_keywords(reference))
        overlap = len(answer_terms & reference_terms)
        coverage = overlap / max(len(reference_terms), 1)
        length_bonus = min(len(user_answer.strip()) // 40, 2) * 5
        score = max(30, min(95, int(45 + coverage * 40 + length_bonus)))
        missing_points = [
            term
            for term in list(reference_terms - answer_terms)[:4]
            if len(term) >= 2
        ] or ["可以补充更完整的原理、边界条件或实践例子"]
        return InterviewFeedback(
            score=score,
            missing_points=missing_points,
            reference_answer=reference,
            follow_up=f"请结合一个实际项目场景，继续说明：{question}",
            comment="已根据参考答案关键词覆盖度和回答完整度给出规则兜底评分。",
            next_action="continue_project" if score < 65 else "next_question",
            next_stage="project_follow_up" if score < 65 else None,
            decision_reason="低于 65 分时优先继续追问项目场景，否则进入下一题。",
        )

    def _rule_based_summary(
        self,
        *,
        target: str | None,
        answered_items: list[dict[str, Any]],
    ) -> InterviewSummaryResult:
        scores = [
            int(item.get("feedback", {}).get("score", 0))
            for item in answered_items
            if item.get("feedback")
        ]
        average = int(sum(scores) / len(scores)) if scores else 0
        target_text = f"，面向{target}" if target else ""
        tag_scores: dict[str, list[int]] = {}
        project_scores: dict[str, list[int]] = {}
        for item in answered_items:
            score = int((item.get("feedback") or {}).get("score", 0))
            for tag in item.get("tags") or []:
                tag_scores.setdefault(str(tag), []).append(score)
            project_name = item.get("related_project")
            if project_name:
                project_scores.setdefault(str(project_name), []).append(score)
        next_steps = ["复盘低分题", "补充项目案例", "按标签继续做专项练习"]
        return InterviewSummaryResult(
            score=average,
            strengths=["能完成核心问题作答", "已经形成可继续追问的表达基础"] if scores else [],
            weaknesses=["部分答案需要补充关键术语和场景化说明"] if scores else ["尚未提交回答"],
            next_steps=next_steps,
            project_performance=[
                ProjectPerformanceResult(
                    project_name=project_name,
                    score=int(sum(project_item_scores) / len(project_item_scores)),
                    comment="根据项目相关追问的回答质量汇总。",
                )
                for project_name, project_item_scores in project_scores.items()
                if project_item_scores
            ],
            knowledge_performance=[
                KnowledgePerformanceResult(
                    tag=tag,
                    mastery=round(sum(tag_item_scores) / len(tag_item_scores) / 100, 2),
                )
                for tag, tag_item_scores in tag_scores.items()
                if tag_item_scores
            ],
            review_plan=[
                ReviewPlanItemResult(topic=step, suggestion=step)
                for step in next_steps
            ],
            comment=f"本次普通面试共完成 {len(scores)} 题{target_text}，平均分 {average}。",
        )


def _extract_block_id(line: str) -> str | None:
    if line.startswith("[") and "]" in line:
        return line[1 : line.index("]")]
    return None


def _parse_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("LLM response must be a JSON object", stripped, 0)
    return parsed


def _validate_llm_response[ModelT: BaseModel](
    model: type[ModelT],
    payload: dict[str, Any],
    message: str,
) -> ModelT:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise AppError("LLM_INVALID_RESPONSE", message, status_code=502) from exc


def bank_ranking_tool_schema() -> dict[str, Any]:
    recommendation_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "bank_id": {"type": "string"},
            "name": {"type": "string"},
            "score": {"type": "integer"},
            "reasons": {"type": "array", "items": {"type": "string"}},
            "matched_keywords": {"type": "array", "items": {"type": "string"}},
            "question_count": {"type": "integer"},
        },
        "required": [
            "bank_id",
            "name",
            "score",
            "reasons",
            "matched_keywords",
            "question_count",
        ],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "strategy": {"type": "string"},
            "reason": {"type": "string"},
            "recommendations": {"type": "array", "items": recommendation_schema},
        },
        "required": ["strategy", "reason", "recommendations"],
    }


def interview_selection_tool_schema() -> dict[str, Any]:
    item_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "question_id": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["question_id", "reason"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "strategy": {"type": "string"},
            "reason": {"type": "string"},
            "items": {"type": "array", "items": item_schema},
        },
        "required": ["strategy", "reason", "items"],
    }


def interview_plan_tool_schema() -> dict[str, Any]:
    stage_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "stage": {"type": "string"},
            "title": {"type": "string"},
            "objective": {"type": "string"},
            "question_count": {"type": "integer"},
            "focus": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["stage", "title", "objective", "question_count", "focus"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "flow_mode": {"type": "string"},
            "strategy": {"type": "string"},
            "reason": {"type": "string"},
            "stages": {"type": "array", "items": stage_schema},
        },
        "required": ["flow_mode", "strategy", "reason", "stages"],
    }


def interview_feedback_tool_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score": {"type": "integer"},
            "missing_points": {"type": "array", "items": {"type": "string"}},
            "reference_answer": {"type": "string"},
            "follow_up": {"type": ["string", "null"]},
            "comment": {"type": "string"},
            "next_action": {"type": "string"},
            "next_stage": {"type": ["string", "null"]},
            "decision_reason": {"type": ["string", "null"]},
        },
        "required": [
            "score",
            "missing_points",
            "reference_answer",
            "follow_up",
            "comment",
            "next_action",
            "next_stage",
            "decision_reason",
        ],
    }


def interview_summary_tool_schema() -> dict[str, Any]:
    project_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "project_name": {"type": "string"},
            "score": {"type": "integer"},
            "comment": {"type": "string"},
        },
        "required": ["project_name", "score", "comment"],
    }
    knowledge_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "tag": {"type": "string"},
            "mastery": {"type": "number"},
        },
        "required": ["tag", "mastery"],
    }
    review_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "topic": {"type": "string"},
            "suggestion": {"type": "string"},
        },
        "required": ["topic", "suggestion"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "score": {"type": "integer"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "weaknesses": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "project_performance": {"type": "array", "items": project_schema},
            "knowledge_performance": {"type": "array", "items": knowledge_schema},
            "review_plan": {"type": "array", "items": review_schema},
            "comment": {"type": "string"},
        },
        "required": [
            "score",
            "strengths",
            "weaknesses",
            "next_steps",
            "project_performance",
            "knowledge_performance",
            "review_plan",
            "comment",
        ],
    }


def _split_text_chunks(text: str, max_chars: int = 2800) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in lines:
        line_len = len(line) + 1
        if current and current_len + line_len > max_chars:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len
    if current:
        chunks.append("\n".join(current))
    return chunks or [text]


def _dedupe_questions(items: list[ExtractedQuestion]) -> list[ExtractedQuestion]:
    deduped: list[ExtractedQuestion] = []
    seen: set[str] = set()
    for item in items:
        key = re.sub(r"\s+", "", item.question.lower().strip(" ?？。"))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _build_item(question: str, answer: str, source_blocks: list[str]) -> ExtractedQuestion:
    tags = ["AI抽取"]
    if "React" in question or "react" in question:
        tags.append("React")
    if "事件循环" in question:
        tags.append("JavaScript")
    return ExtractedQuestion(
        question=question,
        answer=answer or None,
        tags=tags,
        difficulty_score=50,
        difficulty_label="medium",
        source_block_ids=list(dict.fromkeys(source_blocks)),
        confidence=0.75,
    )


def _keywords(text: str) -> list[str]:
    normalized = (
        text.replace("，", " ")
        .replace("。", " ")
        .replace(",", " ")
        .replace(".", " ")
        .replace("、", " ")
        .replace("：", " ")
        .replace(":", " ")
    )
    return [part.strip().lower() for part in normalized.split() if part.strip()]


def _profile_terms(resume_summary: dict[str, Any] | None, target: str | None) -> list[str]:
    parts: list[str] = [target or ""]
    if resume_summary:
        parts.extend(str(skill) for skill in resume_summary.get("skills") or [])
        parts.extend(
            str(direction) for direction in resume_summary.get("follow_up_directions") or []
        )
        for project in resume_summary.get("projects") or []:
            if not isinstance(project, dict):
                continue
            parts.append(str(project.get("name") or ""))
            parts.append(str(project.get("description") or ""))
            parts.extend(str(tech) for tech in project.get("technologies") or [])
        for experience in resume_summary.get("experience") or []:
            if not isinstance(experience, dict):
                continue
            parts.append(str(experience.get("title") or ""))
            parts.append(str(experience.get("description") or ""))
    return list(dict.fromkeys(_keywords(" ".join(parts))))
