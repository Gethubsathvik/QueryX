"""API gateway (port 8000): the only public entry point in microservices mode.

Serves the UI and routes /api/* to the right internal service. Internal endpoints
(/internal/*) are never exposed because only the routes listed below are proxied.

    python -m uvicorn services.gateway.main:app --port 8000
"""

from __future__ import annotations

import asyncio
import os

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import VIEWS_DIR

ROUTES = (
    ("/api/ask", "query"),
    ("/api/sql", "query"),
    ("/api/charts", "chart"),
    ("/api/chart", "chart"),
    ("/api/examples", "query"),
    ("/api/schema", "data"),
    ("/api/upload", "data"),
    ("/api/history", "history"),
)
ENV_URLS = {
    "query": ("QUERY_SERVICE_URL", "http://127.0.0.1:8001"),
    "data": ("DATA_SERVICE_URL", "http://127.0.0.1:8002"),
    "history": ("HISTORY_SERVICE_URL", "http://127.0.0.1:8003"),
    "chart": ("CHART_SERVICE_URL", "http://127.0.0.1:8004"),
}


def default_upstreams() -> dict[str, httpx.AsyncClient]:
    return {
        name: httpx.AsyncClient(base_url=os.environ.get(var, default), timeout=60.0)
        for name, (var, default) in ENV_URLS.items()
    }


def create_app(upstreams: dict[str, httpx.AsyncClient] | None = None) -> FastAPI:
    upstreams = upstreams or default_upstreams()
    app = FastAPI(title="QueryX Gateway")

    @app.get("/api/health")
    async def health():
        async def probe(name: str, client: httpx.AsyncClient):
            try:
                r = await client.get("/api/health", timeout=3.0)
                return name, (r.json() if r.status_code == 200 else {"status": "error"})
            except (httpx.HTTPError, ValueError):
                return name, {"status": "down"}

        results = dict(
            await asyncio.gather(*(probe(n, c) for n, c in upstreams.items()))
        )
        ok = all(v.get("status") == "ok" for v in results.values())
        return {
            "status": "ok" if ok else "degraded",
            "mode": "microservices",
            "services": results,
        }

    @app.api_route("/api/{path:path}", methods=["GET", "POST"])
    async def proxy(path: str, request: Request):
        full = "/api/" + path
        target = next(
            (
                svc
                for prefix, svc in ROUTES
                if full == prefix or full.startswith(prefix + "/")
            ),
            None,
        )
        if target is None:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        headers = {
            k: v for k in ("content-type", "accept") if (v := request.headers.get(k))
        }
        url = full + (f"?{request.url.query}" if request.url.query else "")
        try:
            r = await upstreams[target].request(
                request.method, url, content=await request.body(), headers=headers
            )
        except httpx.HTTPError:
            return JSONResponse(
                {"detail": f"{target} service unavailable"}, status_code=503
            )
        return Response(
            content=r.content,
            status_code=r.status_code,
            headers={"content-type": r.headers.get("content-type", "application/json")},
        )

    @app.get("/")
    def index():
        return FileResponse(VIEWS_DIR / "index.html")

    app.mount("/views", StaticFiles(directory=VIEWS_DIR), name="views")
    return app


_app: FastAPI | None = None


def __getattr__(name: str):
    global _app
    if name == "app":
        if _app is None:
            _app = create_app()
        return _app
    raise AttributeError(name)
