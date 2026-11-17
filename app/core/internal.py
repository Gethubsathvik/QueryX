"""Shared-secret protection for service-to-service (internal) endpoints."""
from __future__ import annotations

import hmac
from collections.abc import Callable

from fastapi import Header, HTTPException

HEADER_NAME = "X-Internal-Token"


def require_internal_token(token: str) -> Callable:
    """FastAPI dependency factory. If `token` is empty, internal endpoints are open (dev only)."""

    def dependency(x_internal_token: str | None = Header(default=None)) -> None:
        if token and not hmac.compare_digest(x_internal_token or "", token):
            raise HTTPException(401, "invalid internal token")

    return dependency


def auth_headers(token: str) -> dict[str, str]:
    return {HEADER_NAME: token} if token else {}
