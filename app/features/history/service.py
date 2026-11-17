"""History service: business logic over the history repository."""
from __future__ import annotations

from .repository import History


class HistoryService:
    def __init__(self, repo: History):
        self.repo = repo

    def add(self, question: str, sql: str, row_count: int, engine: str) -> None:
        self.repo.add(question, sql, row_count, engine)

    def recent(self, limit: int = 20) -> list[dict]:
        return self.repo.recent(max(1, min(limit, 100)))
