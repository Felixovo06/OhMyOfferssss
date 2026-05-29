from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QuestionBankCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    group_id: str | None = None
    default_tags: list[str] = Field(default_factory=list, max_length=12)
    target_roles: list[str] = Field(default_factory=list, max_length=12)
    target_positions: list[str] = Field(default_factory=list, max_length=12)
    skill_keywords: list[str] = Field(default_factory=list, max_length=24)
    domains: list[str] = Field(default_factory=list, max_length=12)
    domain_tags: list[str] = Field(default_factory=list, max_length=12)
    semantic_profile: dict[str, Any] = Field(default_factory=dict)


class QuestionBankUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    default_tags: list[str] | None = Field(default=None, max_length=12)
    target_roles: list[str] | None = Field(default=None, max_length=12)
    target_positions: list[str] | None = Field(default=None, max_length=12)
    skill_keywords: list[str] | None = Field(default=None, max_length=24)
    domains: list[str] | None = Field(default=None, max_length=12)
    domain_tags: list[str] | None = Field(default=None, max_length=12)
    semantic_profile: dict[str, Any] | None = None


class QuestionBankOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    group_id: str | None
    created_by_id: str
    owner_id: str
    default_tags: list[str]
    target_roles: list[str]
    target_positions: list[str]
    skill_keywords: list[str]
    domains: list[str]
    domain_tags: list[str]
    semantic_profile: dict[str, Any]
    tags: list[str]
    scope: str
    question_count: int
    created_at: datetime
    updated_at: datetime
