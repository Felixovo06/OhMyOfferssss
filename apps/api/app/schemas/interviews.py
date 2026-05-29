from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.questions import QuestionOut


class InterviewCreate(BaseModel):
    mode: str | None = Field(default=None, pattern="^(normal|custom)$")
    bank_ids: list[str] = Field(min_length=1, max_length=10)
    tags: list[str] = Field(default_factory=list, max_length=12)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_min: int | None = Field(default=None, ge=0, le=100)
    difficulty_max: int | None = Field(default=None, ge=0, le=100)
    question_count: int = Field(default=5, ge=1, le=20)
    goal: str | None = Field(default=None, max_length=300)
    target: str | None = Field(default=None, max_length=300)
    title: str | None = Field(default=None, max_length=160)
    resume_id: str | None = None


class InterviewQuestionFeedback(BaseModel):
    score: int = Field(ge=0, le=100)
    missing_points: list[str] = Field(default_factory=list)
    reference_answer: str
    follow_up: str | None = None
    comment: str


class InterviewSummary(BaseModel):
    score: int = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
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
    config: dict
    strategy: str
    selection_reason: str
    status: str
    summary: InterviewSummary | None = None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[InterviewItemOut] = Field(default_factory=list)
