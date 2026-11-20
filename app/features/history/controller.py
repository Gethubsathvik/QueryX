"""History controller: public HTTP route."""

from __future__ import annotations

from fastapi import APIRouter

from .service import HistoryService


def build_router(service: HistoryService) -> APIRouter:
    router = APIRouter()

    @router.get("/api/history")
    def get_history(limit: int = 20):
        return {"items": service.recent(limit)}

    return router
