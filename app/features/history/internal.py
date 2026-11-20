"""Internal (service-to-service) routes of the history feature. Mounted only in microservices mode."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ...core.internal import require_internal_token
from .service import HistoryService


class HistoryEntry(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    sql: str
    row_count: int
    engine: str


def build_internal_router(service: HistoryService, token: str) -> APIRouter:
    router = APIRouter(
        prefix="/internal", dependencies=[Depends(require_internal_token(token))]
    )

    @router.post("/history")
    def add(entry: HistoryEntry):
        service.add(entry.question, entry.sql, entry.row_count, entry.engine)
        return {"ok": True}

    return router
