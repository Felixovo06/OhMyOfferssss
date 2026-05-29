from typing import TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class ApiResponse[DataT](BaseModel):
    success: bool = True
    data: DataT
    request_id: str | None = None
