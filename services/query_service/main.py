"""Query service (port 8001): question -> SQL (LLM) -> asks the data service to execute it.

It never touches a database directly; it talks to the data and history services over HTTP.

    python -m uvicorn services.query_service.main:app --port 8001
"""

from __future__ import annotations

import os

import httpx
from fastapi import FastAPI

from app.core.config import Settings
from app.features.ask import controller
from app.features.ask.generators import get_generator
from app.features.ask.service import AskService
from app.features.data.client import RemoteDataClient
from app.features.history.client import RemoteHistoryClient


def create_app(
    data_client=None,
    history_client=None,
    generator=None,
    settings: Settings | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    if data_client is None:
        data_client = RemoteDataClient(
            httpx.Client(
                base_url=os.environ.get("DATA_SERVICE_URL", "http://127.0.0.1:8002"),
                timeout=30.0,
            ),
            settings.internal_token,
        )
    if history_client is None:
        history_client = RemoteHistoryClient(
            httpx.Client(
                base_url=os.environ.get("HISTORY_SERVICE_URL", "http://127.0.0.1:8003"),
                timeout=10.0,
            ),
            settings.internal_token,
        )
    gen = generator or get_generator(settings)
    service = AskService(gen, data_client, history_client)

    app = FastAPI(title="QueryX Query Service")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "query", "engine": gen.name}

    app.include_router(controller.build_router(service))
    return app


_app: FastAPI | None = None


def __getattr__(name: str):
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
