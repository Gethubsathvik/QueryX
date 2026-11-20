"""Data service (port 8002): owns the data database, validates and executes SQL.

python -m uvicorn services.data_service.main:app --port 8002
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.core.config import Settings
from app.features.data import controller, internal
from app.features.data.repository import Database
from app.features.data.service import DataService


def create_app(
    data_dir: Path | str | None = None, internal_token: str | None = None
) -> FastAPI:
    settings = Settings.from_env(data_dir)
    token = settings.internal_token if internal_token is None else internal_token
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    db = Database(settings.data_dir / "queryx.db")
    db.ensure_seeded()
    service = DataService(db, settings.max_rows, settings.query_timeout)

    app = FastAPI(title="QueryX Data Service")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "data"}

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
