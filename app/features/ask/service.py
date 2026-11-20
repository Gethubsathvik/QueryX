"""Ask service: orchestrates question -> SQL -> validated execution -> chart -> history.

It depends only on three collaborators with simple interfaces, so the same code runs
in the monolith (in-process objects) and in microservices mode (HTTP clients):
  generator: generate(question, schema_text), repair(...), name
  data:      schema_text(), execute(sql)            (DataService or RemoteDataClient)
  history:   add(question, sql, row_count, engine)  (HistoryService or RemoteHistoryClient)
"""

from __future__ import annotations

from ...core.errors import UpstreamError
from ..charts.service import suggest_chart
from ..data.repository import QueryError, QueryTimeout
from .generators import GenerationError, NoAnswer


class AskService:
    def __init__(self, generator, data, history):
        self.generator = generator
        self.data = data
        self.history = history

    def ask(self, question: str) -> dict:
        question = question.strip()
        if len(question) < 3:
            raise NoAnswer("Please ask a longer question.")

        schema_text = self.data.schema_text()
        generated = self.generator.generate(question, schema_text)

        attempts = 1
        while True:
            try:
                result = self.data.execute(
                    generated.sql
                )  # validates, then runs read-only
                break
            except QueryTimeout:
                raise
            except QueryError as e:  # UnsafeSQLError is deliberately NOT repaired
                if attempts >= 2:
                    raise QueryError(f"The generated SQL failed to run: {e}") from e
                try:
                    generated = self.generator.repair(
                        question, schema_text, generated.sql, str(e)
                    )
                except (NoAnswer, GenerationError) as e2:
                    raise QueryError(f"The generated SQL failed to run: {e}") from e2
                attempts += 1

        try:
            self.history.add(
                question, result["sql"], result["row_count"], self.generator.name
            )
        except UpstreamError:
            pass  # history is best-effort; never fail an answer because of it

        return {
            "question": question,
            "sql": result["sql"],
            "explanation": generated.explanation,
            "engine": self.generator.name,
            "attempts": attempts,
            "chart": suggest_chart(result["columns"], result["rows"]),
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "truncated": result["truncated"],
            "elapsed_ms": result["elapsed_ms"],
        }

    def run_sql(self, sql: str) -> dict:
        """Run SQL typed or edited by the user through the same safety pipeline (no LLM, no auto-repair)."""
        sql = sql.strip()
        if not sql:
            raise NoAnswer("Type a SQL query first.")
        result = self.data.execute(
            sql
        )  # validates, then runs read-only with row and time limits
        try:
            self.history.add(
                f"[SQL] {sql[:120]}", result["sql"], result["row_count"], "manual"
            )
        except UpstreamError:
            pass
        return {
            "question": "",
            "sql": result["sql"],
            "explanation": "Ran your SQL.",
            "engine": "manual",
            "attempts": 1,
            "chart": suggest_chart(result["columns"], result["rows"]),
            "columns": result["columns"],
            "rows": result["rows"],
            "row_count": result["row_count"],
            "truncated": result["truncated"],
            "elapsed_ms": result["elapsed_ms"],
        }
