"""CLI entry point for the evaluation harness:  python -m app.evaluate"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from .core.config import Settings
from .features.ask.generators import get_generator
from .features.data.repository import Database
from .features.evaluation.service import GOLDEN_PATH, run_eval

__all__ = ["GOLDEN_PATH", "main", "run_eval"]


def main() -> int:
    cases = json.loads(GOLDEN_PATH.read_text())
    generator = get_generator(Settings.from_env())
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(Path(tmp) / "eval.db")
        db.ensure_seeded()
        report = run_eval(db, generator, cases)
    out = GOLDEN_PATH.parent / "report.json"
    out.write_text(json.dumps(report, indent=2))
    print(f"Engine: {report['engine']}")
    for c in report["cases"]:
        print(
            f"  [{'PASS' if c['passed'] else 'FAIL'}] {c['question']}"
            + (f"  ({c['error']})" if c["error"] else "")
        )
    print(
        f"Execution accuracy: {report['passed']}/{report['total']} = {report['execution_accuracy']}%"
    )
    print(f"Report written to {out}")
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
