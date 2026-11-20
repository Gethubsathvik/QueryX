"""HTTP client for the history service (used by the query service in microservices mode)."""

from __future__ import annotations

import httpx

from ...core.errors import UpstreamError
from ...core.internal import auth_headers


class RemoteHistoryClient:
    def __init__(self, client: httpx.Client, token: str = ""):
        self.client = client
        self.headers = auth_headers(token)

    def add(self, question: str, sql: str, row_count: int, engine: str) -> None:
        try:
            r = self.client.post(
                "/internal/history",
                headers=self.headers,
                json={
                    "question": question,
                    "sql": sql,
                    "row_count": row_count,
                    "engine": engine,
                },
            )
        except httpx.HTTPError as e:
            raise UpstreamError("history service unavailable") from e
        if r.status_code != 200:
            raise UpstreamError(f"history service returned {r.status_code}")
