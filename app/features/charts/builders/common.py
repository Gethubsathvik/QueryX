"""Helpers shared by every chart builder. Builders return plain Plotly figure dicts."""

from __future__ import annotations

import datetime as dt
import math

from ..errors import ChartError
from ..table import Table, fmt_label, parse_date

# Okabe-Ito: distinguishable for the common kinds of colour-blindness.
PALETTE = [
    "#0072B2",
    "#E69F00",
    "#009E73",
    "#D55E00",
    "#CC79A7",
    "#56B4E9",
    "#999999",
    "#F0E442",
]
MAX_GROUPS = 30


def hex_rgba(h: str, alpha: float) -> str:
    h = h.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def fmt_num(v: float) -> str:
    a = abs(v)
    if a >= 1000:
        return f"{v:,.0f}"
    if a >= 10:
        return f"{v:,.1f}"
    return f"{v:.3g}"


def clean(obj):
    """Make a figure JSON-safe: NaN/Infinity become None (null)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    return obj


def fig(data: list, layout: dict | None = None, notes: list[str] | None = None) -> dict:
    base = {"colorway": PALETTE}
    base.update(layout or {})
    return {"data": data, "layout": base, "notes": notes or []}


def ax(title: str | None = None, **kw) -> dict:
    out = dict(kw)
    if title is not None:
        out["title"] = {"text": title}
    return out


def aggregate(values: list, how: str):
    if how == "count":
        return float(len(values))
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return {"sum": sum, "min": min, "max": max, "mean": lambda xs: sum(xs) / len(xs)}[
        how
    ](nums)


def x_order(t: Table, col: str, raws: list) -> list:
    """Dates and numbers are sorted; text keeps first-appearance order. Nulls go last."""
    present = [r for r in raws if r is not None]
    p = t.primary(col)
    if p == "date":
        present.sort(
            key=lambda v: (
                parse_date(v) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            )
        )
    elif p == "number":
        present.sort()
    return present + ([None] if None in raws else [])


def x_label(t: Table, col: str, raw):
    if raw is None:
        return "(null)"
    return raw if t.primary(col) in ("date", "number") else fmt_label(raw)


def pivot(t: Table, x: str, ycols: list[str], group: list[str], how: str):
    """Aggregate y by x. Returns (x labels, [(series name, values)]); one series per group or per y column."""
    xs = t.values(x)
    keys = x_order(t, x, list(dict.fromkeys(xs)))
    pos = {k: i for i, k in enumerate(keys)}
    labels = [x_label(t, x, k) for k in keys]
    series = []
    if group:
        g, y = t.values(group[0]), t.numbers(ycols[0])
        names = list(dict.fromkeys(fmt_label(v) for v in g))
        if len(names) > MAX_GROUPS:
            raise ChartError(
                f"'{group[0]}' has {len(names)} distinct values; pick a column with at most {MAX_GROUPS}."
            )
        cells = {n: [[] for _ in keys] for n in names}
        for xv, gv, yv in zip(xs, g, y):
            cells[fmt_label(gv)][pos[xv]].append(yv)
        for n in names:
            series.append((n, [aggregate(c, how) if c else None for c in cells[n]]))
    else:
        for col in ycols:
            cells = [[] for _ in keys]
            for xv, yv in zip(xs, t.numbers(col)):
                cells[pos[xv]].append(yv)
            series.append((col, [aggregate(c, how) if c else None for c in cells]))
    if len(keys) > 2000:
        raise ChartError("Too many distinct X values to draw; aggregate in SQL first.")
    return labels, series


def grid(t: Table, xc: str, yc: str, vc: str, how: str):
    """Pivot to a matrix z[y][x]. Returns (x labels, y labels, z)."""
    xv, yv, nv = t.values(xc), t.values(yc), t.numbers(vc)
    xk = x_order(t, xc, list(dict.fromkeys(xv)))
    yk = x_order(t, yc, list(dict.fromkeys(yv)))
    if len(xk) > 200 or len(yk) > 200:
        raise ChartError(
            "Too many categories for a grid (limit 200 per axis); aggregate in SQL first."
        )
    xi, yi = {k: i for i, k in enumerate(xk)}, {k: i for i, k in enumerate(yk)}
    cells: dict = {}
    for a, b, v in zip(xv, yv, nv):
        cells.setdefault((yi[b], xi[a]), []).append(v)
    z = [[None] * len(xk) for _ in yk]
    for (r, c), vs in cells.items():
        z[r][c] = aggregate(vs, how)
    return [fmt_label(k) for k in xk], [fmt_label(k) for k in yk], z


def numeric_frame(t: Table, cols: list[str]):
    """Rows where every listed column is numeric. Returns (row indices, {col: floats})."""
    arrs = [t.numbers(c) for c in cols]
    idx = [i for i in range(len(t)) if all(a[i] is not None for a in arrs)]
    return idx, {c: [a[i] for i in idx] for c, a in zip(cols, arrs)}


def group_positions(t: Table, group: list[str], idx: list[int]) -> dict[str, list[int]]:
    """Map group label -> positions (within idx). One group called '' when no group column."""
    if not group:
        return {"": list(range(len(idx)))}
    g = t.values(group[0])
    out: dict[str, list[int]] = {}
    for pos, i in enumerate(idx):
        out.setdefault(fmt_label(g[i]), []).append(pos)
    if len(out) > MAX_GROUPS:
        raise ChartError(
            f"'{group[0]}' has {len(out)} distinct values; pick a column with at most {MAX_GROUPS}."
        )
    return out


def sort_labels(labels) -> list[str]:
    def key(s):
        try:
            return (0, float(s), s)
        except ValueError:
            return (1, 0.0, s)

    return sorted(set(labels), key=key)


def tick_subset(n: int, target: int = 14) -> list[int]:
    step = max(1, math.ceil(n / target))
    return list(range(0, n, step))
