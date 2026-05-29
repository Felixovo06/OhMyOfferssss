import json

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings


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


class InterviewSelectionItem(BaseModel):
    question_id: str
    reason: str


class InterviewSelection(BaseModel):
    strategy: str
    reason: str
    items: list[InterviewSelectionItem]


class InterviewFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_points: list[str] = Field(default_factory=list)
    reference_answer: str
    follow_up: str | None = None
    comment: str


class InterviewSummaryResult(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    comment: str


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def extract_questions_from_text(self, normalized_text: str) -> ExtractedQuestionList:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_extract(normalized_text)

        response = httpx.post(
            f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "从面试资料中抽取题目，严格返回 JSON：{\"items\": [...]}",
                    },
                    {"role": "user", "content": normalized_text},
                ],
                "response_format": {"type": "json_object"},
                "thinking": {"enabled": self.settings.llm_thinking_enabled},
            },
            timeout=60,
        )
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return ExtractedQuestionList.model_validate(json.loads(content))

    def select_interview_questions(
        self,
        candidates: list[InterviewCandidate],
        *,
        question_count: int,
        target: str | None,
    ) -> InterviewSelection:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_select(candidates, question_count=question_count, target=target)

        payload = self._chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试官。请从候选题中选择普通面试题，严格返回 JSON："
                        "{\"strategy\": string, \"reason\": string, "
                        "\"items\": [{\"question_id\": string, \"reason\": string}]}"
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
        )
        return InterviewSelection.model_validate(payload)

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

        payload = self._chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试反馈助手。请评分并给出缺失点、参考表达和追问，严格返回 JSON："
                        "{\"score\": number, \"missing_points\": string[], "
                        "\"reference_answer\": string, \"follow_up\": string|null, "
                        "\"comment\": string}"
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
        )
        return InterviewFeedback.model_validate(payload)

    def summarize_interview(
        self,
        *,
        target: str | None,
        answered_items: list[dict],
    ) -> InterviewSummaryResult:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            return self._rule_based_summary(target=target, answered_items=answered_items)

        payload = self._chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "你是面试总结助手。请总结整体表现，严格返回 JSON："
                        "{\"score\": number, \"strengths\": string[], \"weaknesses\": string[], "
                        "\"next_steps\": string[], \"comment\": string}"
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
        )
        return InterviewSummaryResult.model_validate(payload)

    def _chat_json(self, messages: list[dict[str, str]]) -> dict:
        response = httpx.post(
            f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "thinking": {"enabled": self.settings.llm_thinking_enabled},
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return json.loads(content)

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
        )

    def _rule_based_summary(
        self,
        *,
        target: str | None,
        answered_items: list[dict],
    ) -> InterviewSummaryResult:
        scores = [
            int(item.get("feedback", {}).get("score", 0))
            for item in answered_items
            if item.get("feedback")
        ]
        average = int(sum(scores) / len(scores)) if scores else 0
        target_text = f"，面向{target}" if target else ""
        return InterviewSummaryResult(
            score=average,
            strengths=["能完成核心问题作答", "已经形成可继续追问的表达基础"] if scores else [],
            weaknesses=["部分答案需要补充关键术语和场景化说明"] if scores else ["尚未提交回答"],
            next_steps=["复盘低分题", "补充项目案例", "按标签继续做专项练习"],
            comment=f"本次普通面试共完成 {len(scores)} 题{target_text}，平均分 {average}。",
        )


def _extract_block_id(line: str) -> str | None:
    if line.startswith("[") and "]" in line:
        return line[1 : line.index("]")]
    return None


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
