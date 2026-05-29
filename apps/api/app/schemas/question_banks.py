from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionBankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    group_id: str | None = None
    default_tags: list[str] = Field(default_factory=list, max_length=12)


class QuestionBankUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    default_tags: list[str] | None = Field(default=None, max_length=12)


class QuestionBankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    group_id: str | None
    created_by_id: str
    owner_id: str
    default_tags: list[str]
    tags: list[str]
    scope: str
    question_count: int
    created_at: datetime
    updated_at: datetime
