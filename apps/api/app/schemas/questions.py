from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QuestionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str | None = Field(default=None, min_length=1)
    content: str | None = None
    answer: str | None = None
    tags: list[str] = Field(default_factory=list, max_length=12)
    difficulty_score: int | None = Field(default=None, ge=0, le=100)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_label: str | None = None
    source_type: str = "manual"
    source_block_ids: list[str] = Field(default_factory=list)
    enabled: bool = True
    status: str | None = None

    @field_validator("difficulty_label")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        if value is not None and value not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty_label must be easy, medium or hard")
        return value


class QuestionUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    question: str | None = Field(default=None, min_length=1)
    content: str | None = Field(default=None, min_length=1)
    answer: str | None = None
    tags: list[str] | None = Field(default=None, max_length=12)
    difficulty_score: int | None = Field(default=None, ge=0, le=100)
    difficulty: int | None = Field(default=None, ge=0, le=100)
    difficulty_label: str | None = None
    enabled: bool | None = None
    status: str | None = None

    @field_validator("difficulty_label")
    @classmethod
    def validate_label(cls, value: str | None) -> str | None:
        if value is not None and value not in {"easy", "medium", "hard"}:
            raise ValueError("difficulty_label must be easy, medium or hard")
        return value


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bank_id: str
    source_id: str | None
    question: str
    content: str
    answer: str | None
    tags: list[str]
    difficulty_score: int | None
    difficulty: int | None
    difficulty_label: str | None
    source_type: str
    source_block_ids: list[str]
    enabled: bool
    status: str
    created_at: datetime
    updated_at: datetime


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
    updated_at: datetime
