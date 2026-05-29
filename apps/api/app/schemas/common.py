from typing import TypeVar

from pydantic import BaseModel, Field

from app.core.middleware import get_request_id

DataT = TypeVar("DataT")


class ApiResponse[DataT](BaseModel):
    success: bool = True
    data: DataT
    request_id: str | None = Field(default_factory=get_request_id)
