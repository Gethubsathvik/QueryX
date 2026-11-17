"""Execution-accuracy evaluation logic.

For every golden case, the generated SQL and the reference SQL are both executed and
their result sets compared (order-insensitive, floats rounded).
"""
from __future__ import annotations

from ...core.config import ROOT
from ..ask.generators import GenerationError, NoAnswer
from ..data.repository import Database, QueryError
from ..data.safety import UnsafeSQLError, validate_sql

GOLDEN_PATH = ROOT / "eval" / "golden.json"


def _normalize(rows: list[list]) -> list[tuple]:
    def norm(v):
        return round(v, 2) if isinstance(v, float) else v
    return sorted((tuple(norm(v) for v in r) for r in rows), key=lambda t: [str(x) for x in t])


def run_eval(db: Database, generator, cases: list[dict]) -> dict:
    schema_text, allowed = db.schema_text(), db.table_names()
    results = []
    for case in cases:
        entry = {"question": case["question"], "passed": False, "error": None}
        try:
            expected = db.run_query(case["reference_sql"], max_rows=10_000)
            generated = generator.generate(case["question"], schema_text)
            safe = validate_sql(generated.sql, allowed)
            actual = db.run_query(safe, max_rows=10_000)
            entry["passed"] = _normalize(actual["rows"]) == _normalize(expected["rows"])
            if not entry["passed"]:
                entry["error"] = "result set differs from reference"
            entry["generated_sql"] = safe
        except (NoAnswer, GenerationError, UnsafeSQLError, QueryError) as e:
            entry["error"] = f"{e.__class__.__name__}: {e}"
        results.append(entry)
    passed = sum(r["passed"] for r in results)
    return {
        "engine": generator.name,
        "total": len(results),
        "passed": passed,
        "execution_accuracy": round(100 * passed / len(results), 1) if results else 0.0,
        "cases": results,
    }
