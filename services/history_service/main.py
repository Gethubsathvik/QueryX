"""History service (port 8003): owns the query-history database.

    python -m uvicorn services.history_service.main:app --port 8003
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.core.config import Settings
from app.features.history import controller, internal
from app.features.history.repository import History
from app.features.history.service import HistoryService


def create_app(data_dir: Path | str | None = None, internal_token: str | None = None) -> FastAPI:
    settings = Settings.from_env(data_dir)
    token = settings.internal_token if internal_token is None else internal_token
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    service = HistoryService(History(settings.data_dir / "history.db"))

    app = FastAPI(title="QueryX History Service")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "history"}

    app.include_router(controller.build_router(service))
    app.include_router(internal.build_internal_router(service, token))
    return app


_app: FastAPI | None = None


def __getattr__(name: str):
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
