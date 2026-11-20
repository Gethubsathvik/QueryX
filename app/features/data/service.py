"""Data service: business logic over the repository. No HTTP code here."""

from __future__ import annotations

from .repository import Database
from .safety import validate_sql


class DataService:
    def __init__(self, db: Database, max_rows: int = 500, timeout_s: float = 3.0):
        self.db = db
        self.max_rows = max_rows
        self.timeout_s = timeout_s

    def table_names(self) -> list[str]:
        return self.db.table_names()

    def schema(self) -> list[dict]:
        return self.db.schema()

    def schema_text(self) -> str:
        return self.db.schema_text()

    def execute(self, sql: str) -> dict:
        """Validate then run `sql`. The only way model-generated SQL reaches the database.

        Raises UnsafeSQLError, QueryTimeout or QueryError.
        """
        safe_sql = validate_sql(sql, self.db.table_names())
        result = self.db.run_query(
            safe_sql, max_rows=self.max_rows, timeout_s=self.timeout_s
        )
        return {"sql": safe_sql, **result}

    def import_csv(self, filename: str, data: bytes) -> dict:
        return self.db.import_csv(filename, data)
