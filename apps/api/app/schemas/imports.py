from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FeishuImportRequest(BaseModel):
    url: str = Field(min_length=1)
    bank_id: str | None = None


class ImportBatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bank_id: str
    source_id: str
    source_url: str
    normalized_text: str
    status: str
    total_count: int
    confirmed_count: int
    error_message: str | None
    items: list["ImportItemOut"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ImportItemUpdate(BaseModel):
    question: str | None = Field(default=None, min_length=1)
    answer: str | None = None
    tags: list[str] | None = Field(default=None, max_length=12)
    difficulty_score: int | None = Field(default=None, ge=0, le=100)
    difficulty_label: str | None = None
    status: str | None = None


class ImportItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    question: str
    content: str
    question_content: str
    answer: str | None
    question_answer: str | None
    tags: list[str]
    difficulty_score: int
    difficulty_label: str
    source_block_ids: list[str]
    confidence: float
    notes: str | None
    status: str
    confirmed_question_id: str | None
    created_at: datetime
    updated_at: datetime


class ImportConfirmResponse(BaseModel):
    confirmed_count: int
    question_ids: list[str]


class ImportDetailOut(BaseModel):
    batch: ImportBatchOut
    items: list[ImportItemOut]
