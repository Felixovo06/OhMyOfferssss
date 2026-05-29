from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.questions import QuestionOut


class InterviewCreate(BaseModel):
    mode: str | None = Field(default=None, pattern="^(normal|custom)$")
    bank_ids: list[str] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=12)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_min: int | None = Field(default=None, ge=0, le=100)
    difficulty_max: int | None = Field(default=None, ge=0, le=100)
    question_count: int = Field(default=5, ge=1, le=20)
    duration_minutes: int | None = Field(default=None, ge=1, le=180)
    goal: str | None = Field(default=None, max_length=300)
    target: str | None = Field(default=None, max_length=300)
    title: str | None = Field(default=None, max_length=160)
    resume_id: str | None = None
    flow_mode: str = Field(
        default="knowledge_first",
        pattern="^(project|knowledge|project_first|knowledge_first)$",
    )
    smart_match: bool = True

    @field_validator("flow_mode")
    @classmethod
    def normalize_flow_mode(cls, value: str) -> str:
        return normalize_flow_mode(value)


class InterviewPlanRequest(BaseModel):
    bank_ids: list[str] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=12)
    question_count: int = Field(default=5, ge=1, le=20)
    duration_minutes: int | None = Field(default=None, ge=1, le=180)
    target: str | None = Field(default=None, max_length=300)
    goal: str | None = Field(default=None, max_length=300)
    resume_id: str | None = None
    flow_mode: str = Field(
        default="knowledge_first",
        pattern="^(project|knowledge|project_first|knowledge_first)$",
    )

    @field_validator("flow_mode")
    @classmethod
    def normalize_flow_mode(cls, value: str) -> str:
        return normalize_flow_mode(value)


class InterviewBankRecommendation(BaseModel):
    bank_id: str
    name: str
    score: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    question_count: int = 0


class InterviewStagePlan(BaseModel):
    stage: str
    title: str
    objective: str
    question_count: int
    focus: list[str] = Field(default_factory=list)


class InterviewPlanOut(BaseModel):
    flow_mode: str
    target: str | None
    recommended_banks: list[InterviewBankRecommendation]
    selected_bank_ids: list[str]
    stages: list[InterviewStagePlan]
    strategy: str
    reason: str


class InterviewQuestionFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_points: list[str] = Field(default_factory=list)
    reference_answer: str
    follow_up: str | None = None
    comment: str
    next_action: str = "next_question"
    next_stage: str | None = None
    decision_reason: str | None = None


class ProjectPerformance(BaseModel):
    project_name: str
    score: int = Field(ge=0, le=100)
    comment: str


class KnowledgePerformance(BaseModel):
    tag: str
    mastery: float = Field(ge=0, le=1)


class ReviewPlanItem(BaseModel):
    topic: str
    suggestion: str


class InterviewSummary(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    project_performance: list[ProjectPerformance] = Field(default_factory=list)
    knowledge_performance: list[KnowledgePerformance] = Field(default_factory=list)
    review_plan: list[ReviewPlanItem] = Field(default_factory=list)
    comment: str


class InterviewAnswerCreate(BaseModel):
    answer: str = Field(min_length=1)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_score: int | None = Field(default=None, ge=0, le=100)


class InterviewDifficultyUpdate(BaseModel):
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_score: int | None = Field(default=None, ge=0, le=100)


class InterviewItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    question_id: str
    position: int
    selection_reason: str
    stage: str
    intent: str
    intention: str
    related_project: str | None = None
    related_skill: str | None = None
    related_skills: list[str] = Field(default_factory=list)
    status: str
    answer: str | None
    feedback: InterviewQuestionFeedback | None = None
    question: QuestionOut
    answered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    mode: str
    target: str | None
    resume_id: str | None = None
    config: dict[str, Any]
    flow_mode: str
    current_stage: str
    stage_plan: list[InterviewStagePlan] = Field(default_factory=list)
    strategy: str
    selection_reason: str
    status: str
    summary: InterviewSummary | None = None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[InterviewItemOut] = Field(default_factory=list)


def normalize_flow_mode(value: str) -> str:
    if value == "project":
        return "project_first"
    if value == "knowledge":
        return "knowledge_first"
    return value
