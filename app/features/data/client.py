"""HTTP client for the data service (used by the query service in microservices mode).

Exposes the same methods as DataService, so AskService does not care which one it gets.
"""

from __future__ import annotations

import httpx

from ...core.errors import UpstreamError
from ...core.internal import auth_headers
from .repository import QueryError, QueryTimeout
from .safety import UnsafeSQLError


class RemoteDataClient:
    def __init__(self, client: httpx.Client, token: str = ""):
        self.client = client
        self.headers = auth_headers(token)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return self.client.request(method, path, headers=self.headers, **kwargs)
        except httpx.HTTPError as e:
            raise UpstreamError("data service unavailable") from e

    def schema_text(self) -> str:
        r = self._request("GET", "/internal/schema-text")
        if r.status_code != 200:
            raise UpstreamError(f"data service returned {r.status_code}")
        return r.json()["schema_text"]

    def execute(self, sql: str) -> dict:
        r = self._request("POST", "/internal/execute", json={"sql": sql})
        if r.status_code == 200:
            return r.json()
        detail = (
            r.json().get("detail", "")
            if r.headers.get("content-type", "").startswith("application/json")
            else ""
        )
        if r.status_code == 400:
            raise UnsafeSQLError(detail)
        if r.status_code == 408:
            raise QueryTimeout(detail)
        if r.status_code == 422:
            raise QueryError(detail)
        raise UpstreamError(f"data service returned {r.status_code}")
