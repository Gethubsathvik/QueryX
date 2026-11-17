"""Monolith composition root: wires every feature together in one process.

    python -m uvicorn app.main:app
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.config import VIEWS_DIR, Settings
from .features.ask import controller as ask_controller
from .features.ask.generators import get_generator
from .features.ask.service import AskService
from .features.charts import controller as charts_controller
from .features.charts.service import ChartService
from .features.data import controller as data_controller
from .features.data.repository import Database
from .features.data.service import DataService
from .features.history import controller as history_controller
from .features.history.repository import History
from .features.history.service import HistoryService


def create_app(data_dir: Path | str | None = None, generator=None) -> FastAPI:
    settings = Settings.from_env(data_dir)
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    db = Database(settings.data_dir / "queryx.db")
    db.ensure_seeded()
    data_service = DataService(db, settings.max_rows, settings.query_timeout)
    history_service = HistoryService(History(settings.data_dir / "history.db"))
    gen = generator or get_generator(settings)
    ask_service = AskService(gen, data_service, history_service)

    app = FastAPI(title="QueryX", version="0.2.0")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "engine": gen.name, "mode": "monolith"}

    app.include_router(data_controller.build_router(data_service))
    app.include_router(history_controller.build_router(history_service))
    app.include_router(ask_controller.build_router(ask_service))
    app.include_router(charts_controller.build_router(ChartService()))

    @app.get("/")
    def index():
        return FileResponse(VIEWS_DIR / "index.html")

    app.mount("/views", StaticFiles(directory=VIEWS_DIR), name="views")
    return app


_app: FastAPI | None = None


def __getattr__(name: str):
    """Lazy `app` so importing this module has no side effects (uvicorn app.main:app still works)."""
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
