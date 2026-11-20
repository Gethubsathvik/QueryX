"""Chart service (port 8004): stateless. Turns a query result into a Plotly figure.

python -m uvicorn services.chart_service.main:app --port 8004
"""

from __future__ import annotations

from fastapi import FastAPI

from app.features.charts import controller
from app.features.charts.service import ChartService


def create_app() -> FastAPI:
    app = FastAPI(title="QueryX Chart Service")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "chart"}

    app.include_router(controller.build_router(ChartService()))
    return app


_app: FastAPI | None = None


def __getattr__(name: str):
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
