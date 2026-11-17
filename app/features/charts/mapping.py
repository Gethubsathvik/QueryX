"""Turn (chart spec + table + optional user choices) into a column mapping, and parse options.

Rules:
- A role present in `requested` is honoured exactly (empty list/None = "none selected").
- A role absent from `requested` is auto-filled from the column types, name hints and cardinality.
- Required roles that end up empty raise ChartError with a human-readable message.
"""
from __future__ import annotations

from .catalog import ChartSpec, Field, Option
from .errors import ChartError
from .table import Table

KIND_WORDS = {"number": "numeric", "date": "date/time", "text": "text", "category": "category"}


def _as_list(value) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value if v not in (None, "")]


def _auto_pick(f: Field, table: Table, used: set[str]) -> list[str]:
    candidates: list[str] = []
    for kind in f.kinds:  # first kind that has any unused column wins
        candidates = [c for c in table.columns if c not in used and kind in table.kinds(c)]
        if candidates:
            break
    if not candidates:
        return []
    if f.hints:
        hinted = [c for c in candidates if any(h in c.lower() for h in f.hints)]
        if hinted:
            candidates = hinted
        elif f.auto == "hint":
            return []
    elif f.auto == "hint":
        return []
    if f.prefer == "low":
        candidates = [c for c in candidates if table.distinct(c) >= 2]
        candidates.sort(key=table.distinct)
    elif f.prefer == "high":
        candidates.sort(key=table.distinct, reverse=True)
    elif f.prefer == "last":
        candidates.reverse()
    return candidates[: (f.max_auto if f.multiple else 1)]


def resolve(spec: ChartSpec, table: Table, requested: dict | None = None) -> dict[str, list[str]]:
    requested = requested or {}
    out: dict[str, list[str]] = {}
    used: set[str] = set()

    for f in spec.fields:  # pass 1: reserve everything the user chose explicitly
        if f.role in requested:
            cols = _as_list(requested[f.role])
            for c in cols:
                table.index(c)  # validates the column exists
            out[f.role] = cols if f.multiple else cols[:1]
            used.update(out[f.role])

    for f in spec.fields:  # pass 2: auto-fill the rest
        if f.role in out:
            continue
        if not f.required and f.auto is False:
            out[f.role] = []
            continue
        out[f.role] = _auto_pick(f, table, used)
        used.update(out[f.role])

    for f in spec.fields:
        need = f.min_count if f.multiple else 1
        if f.required and len(out[f.role]) < need:
            kinds = " or ".join(KIND_WORDS[k] for k in f.kinds if k != "category" or len(f.kinds) == 1)
            count = f"at least {need} " if need > 1 else "a "
            raise ChartError(
                f"{spec.label}: '{f.label}' needs {count}{kinds} column{'s' if need > 1 else ''}, "
                f"but none is available. Pick one in the field selector, or change your SQL.")
    return out


def is_compatible(spec: ChartSpec, table: Table) -> bool:
    try:
        resolve(spec, table)
        return True
    except ChartError:
        return False


def parse_options(spec: ChartSpec, raw: dict | None) -> dict:
    raw = raw or {}
    out = {}
    for o in spec.options:
        out[o.name] = _coerce(o, raw.get(o.name, o.default))
    return out


def _coerce(o: Option, value):
    try:
        if o.type == "bool":
            return value if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on")
        if o.type == "number":
            v = float(value)
            if o.min is not None:
                v = max(o.min, v)
            if o.max is not None:
                v = min(o.max, v)
            return int(v) if float(v).is_integer() else v
        if o.type == "select":
            return value if value in o.choices else o.default
        return "" if value is None else str(value)[:80]
    except (TypeError, ValueError):
        return o.default
