"""A small typed view over a query result (columns + rows) used by every chart builder."""
from __future__ import annotations

import datetime as dt
import math
import re

from .errors import ChartError

DATE_RE = re.compile(r"^\d{4}-\d{2}(-\d{2})?([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$")
LOW_CARDINALITY = 12


def to_float(value) -> float | None:
    """Best-effort numeric conversion. Returns None for null, non-numeric, NaN and infinity."""
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        f = float(value)
    elif isinstance(value, str):
        try:
            f = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return f if math.isfinite(f) else None


def parse_date(value) -> dt.datetime | None:
    """Parse the ISO-like strings SQLite produces (YYYY-MM, YYYY-MM-DD, with optional time)."""
    if not isinstance(value, str) or not DATE_RE.match(value.strip()):
        return None
    s = value.strip().replace("T", " ")
    if len(s) == 7:
        s += "-01"
    try:
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def fmt_label(value) -> str:
    """Stable text label for a category value."""
    if value is None:
        return "(null)"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


class Table:
    def __init__(self, columns: list[str], rows: list[list]):
        self.columns = [str(c) for c in columns]
        self.rows = [list(r) for r in rows]
        self._primary: dict[str, str] = {}
        self._distinct: dict[str, int] = {}

    def __len__(self) -> int:
        return len(self.rows)

    def index(self, name: str) -> int:
        try:
            return self.columns.index(name)
        except ValueError:
            raise ChartError(f"Unknown column '{name}'. Available: {', '.join(self.columns)}") from None

    def values(self, name: str) -> list:
        i = self.index(name)
        return [r[i] if i < len(r) else None for r in self.rows]

    def numbers(self, name: str) -> list[float | None]:
        return [to_float(v) for v in self.values(name)]

    def distinct(self, name: str) -> int:
        if name not in self._distinct:
            self._distinct[name] = len({v for v in self.values(name) if v is not None})
        return self._distinct[name]

    def primary(self, name: str) -> str:
        """'number', 'date' or 'text'."""
        if name not in self._primary:
            vals = [v for v in self.values(name) if v is not None]
            if vals and all(isinstance(v, (bool, int, float)) for v in vals):
                kind = "number"
            elif vals and all(isinstance(v, str) for v in vals) and all(DATE_RE.match(v.strip()) for v in vals):
                kind = "date"
            else:
                kind = "text"
            self._primary[name] = kind
        return self._primary[name]

    def kinds(self, name: str) -> frozenset[str]:
        """Everything this column can act as: number, date, text, category."""
        p = self.primary(name)
        if p == "number":
            ks = {"number"}
            vals = [v for v in self.values(name) if v is not None]
            if vals and all(float(v).is_integer() for v in vals) and self.distinct(name) <= LOW_CARDINALITY:
                ks.add("category")
            return frozenset(ks)
        if p == "date":
            return frozenset({"date", "category"})
        return frozenset({"text", "category"})
