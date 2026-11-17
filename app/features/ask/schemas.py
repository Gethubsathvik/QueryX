"""Request and response models of the ask feature."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    question: str
    sql: str
    explanation: str
    engine: str
    attempts: int
    chart: dict[str, Any]
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: float


class SqlRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)
