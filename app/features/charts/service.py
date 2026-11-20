"""Pick a sensible chart type from a query result."""

from __future__ import annotations

import re

DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def suggest_chart(columns: list[str], rows: list[list]) -> dict:
    if not rows or not columns:
        return {"type": "table"}

    numeric = [
        i
        for i in range(len(columns))
        if any(_is_num(r[i]) for r in rows)
        and all(_is_num(r[i]) or r[i] is None for r in rows)
    ]
    labels = [i for i in range(len(columns)) if i not in numeric]

    if len(rows) == 1 and numeric and not labels:
        return {"type": "metric"}
    if not numeric or not labels:
        return {"type": "table"}

    x = labels[0]
    ys = [columns[i] for i in numeric[:3]]
    is_time = len(rows) >= 2 and all(
        isinstance(r[x], str) and DATE_RE.match(r[x]) for r in rows
    )
    if is_time:
        return {"type": "line", "x": columns[x], "y": ys}
    if len(rows) <= 25:
        return {"type": "bar", "x": columns[x], "y": ys}
    return {"type": "table"}


# ----------------------------------------------------------------------------- chart studio
from .builders import PALETTE, build
from .catalog import CATALOG, catalog_payload, get_spec
from .mapping import is_compatible, parse_options, resolve
from .table import Table

MAX_CHART_ROWS = 5000

# Which gallery chart the quick "auto" suggestion corresponds to.
SUGGESTION_TO_CHART = {"line": "line", "bar": "bar"}


class ChartService:
    """Builds Plotly figures from a query result. Stateless and free of I/O."""

    def catalog(self) -> dict:
        payload = catalog_payload()
        payload["palette"] = PALETTE
        return payload

    def compatible(self, columns: list[str], rows: list[list]) -> list[str]:
        table = Table(columns, rows[:MAX_CHART_ROWS])
        return [c.id for c in CATALOG if is_compatible(c, table)]

    def build(
        self,
        columns: list[str],
        rows: list[list],
        chart: str,
        mapping: dict | None = None,
        options: dict | None = None,
    ) -> dict:
        spec = get_spec(chart)
        table = Table(columns, rows[:MAX_CHART_ROWS])
        if not len(table):
            from .errors import ChartError

            raise ChartError(
                "The query returned no rows, so there is nothing to chart."
            )
        resolved = resolve(spec, table, mapping)
        opts = parse_options(spec, options)
        figure = build(chart, table, resolved, opts)
        return {
            "chart": chart,
            "label": spec.label,
            "mapping": resolved,
            "options": opts,
            "figure": {"data": figure["data"], "layout": figure["layout"]},
            "notes": figure["notes"],
            "truncated": len(rows) > MAX_CHART_ROWS,
        }
