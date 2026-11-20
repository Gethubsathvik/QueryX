"""Performance, process and finance charts: Gantt, bullet, radar, control chart, candlestick, OHLC."""

from __future__ import annotations

import datetime as dt

from .. import stats
from ..errors import ChartError
from ..table import fmt_label, parse_date
from .common import PALETTE, ax, fig, fmt_num


def gantt(t, m, o):
    names, starts, ends = (
        t.values(m["task"][0]),
        t.values(m["start"][0]),
        t.values(m["end"][0]),
    )
    groups = t.values(m["group"][0]) if m.get("group") else None
    rows, bad = [], 0
    for i in range(len(t)):
        a, b = parse_date(starts[i]), parse_date(ends[i])
        if a is None or b is None or b < a:
            bad += 1
            continue
        rows.append((fmt_label(names[i]), a, b, fmt_label(groups[i]) if groups else ""))
    if not rows:
        raise ChartError(
            "The Gantt chart needs rows with a valid start date and an end date on or after it."
        )
    if len(rows) > 80:
        raise ChartError("Too many tasks for a Gantt chart (limit 80).")
    by_group: dict[str, list] = {}
    for r in rows:
        by_group.setdefault(r[3], []).append(r)
    data = []
    for g, rs in by_group.items():
        data.append(
            {
                "type": "bar",
                "orientation": "h",
                "name": g or "Tasks",
                "y": [r[0] for r in rs],
                "x": [max((r[2] - r[1]).total_seconds() * 1000, 3.6e6) for r in rs],
                "base": [r[1].strftime("%Y-%m-%d %H:%M:%S") for r in rs],
                "customdata": [
                    [
                        r[1].strftime("%Y-%m-%d"),
                        r[2].strftime("%Y-%m-%d"),
                        (r[2] - r[1]).days,
                    ]
                    for r in rs
                ],
                "hovertemplate": "<b>%{y}</b><br>%{customdata[0]} to %{customdata[1]} "
                "(%{customdata[2]} days)<extra></extra>",
            }
        )
    layout = {
        "barmode": "overlay",
        "xaxis": ax(None, type="date"),
        "yaxis": ax(None, autorange="reversed"),
        "showlegend": len(by_group) > 1,
    }
    notes = (
        [f"{bad} row(s) with missing dates or end before start were skipped."]
        if bad
        else []
    )
    return fig(data, layout, notes)


def bullet(t, m, o):
    labels, act = t.values(m["label"][0]), t.numbers(m["value"][0])
    tgt = t.numbers(m["target"][0]) if m.get("target") else [None] * len(t)
    mx = t.numbers(m["max"][0]) if m.get("max") else [None] * len(t)
    rows = [i for i in range(len(t)) if act[i] is not None]
    if not rows:
        raise ChartError("The bullet chart needs a numeric 'actual' column.")
    notes = []
    if len(rows) > 12:
        notes.append(f"Showing the first 12 of {len(rows)} measures.")
        rows = rows[:12]
    n, gap = len(rows), 0.07
    h = (1 - gap * (n - 1)) / n
    data = []
    for k, i in enumerate(rows):
        top = 1 - k * (h + gap)
        scale = max(mx[i] or 0, abs(act[i]) * 1.1, abs(tgt[i] or 0) * 1.1) or 1.0
        ind = {
            "type": "indicator",
            "mode": "number+gauge" + ("+delta" if tgt[i] is not None else ""),
            "value": act[i],
            "domain": {"x": [0.28, 0.98], "y": [top - h, top]},
            "title": {"text": fmt_label(labels[i]), "font": {"size": 13}},
            "gauge": {
                "shape": "bullet",
                "axis": {"range": [0, scale]},
                "bar": {"color": PALETTE[0], "thickness": 0.45},
                "steps": [
                    {"range": [0, scale * 0.6], "color": "rgba(127,127,127,0.16)"},
                    {
                        "range": [scale * 0.6, scale * 0.85],
                        "color": "rgba(127,127,127,0.30)",
                    },
                    {"range": [scale * 0.85, scale], "color": "rgba(127,127,127,0.44)"},
                ],
            },
        }
        if tgt[i] is not None:
            ind["delta"] = {"reference": tgt[i]}
            ind["gauge"]["threshold"] = {
                "line": {"color": PALETTE[3], "width": 3},
                "thickness": 0.85,
                "value": tgt[i],
            }
        data.append(ind)
    notes.append(
        "Blue bar = actual, red marker = target, grey bands = 60% / 85% / 100% of the scale."
    )
    return fig(
        data,
        {
            "height": max(240, 78 * n + 70),
            "margin": {"l": 20, "r": 30, "t": 30, "b": 30},
        },
        notes,
    )


def radar(t, m, o):
    label, metrics = m["label"][0], m["metrics"]
    lv = t.values(label)
    nums = {c: t.numbers(c) for c in metrics}
    names = list(dict.fromkeys(fmt_label(v) for v in lv))
    cells = {n: {c: [] for c in metrics} for n in names}
    for i, v in enumerate(lv):
        for c in metrics:
            if nums[c][i] is not None:
                cells[fmt_label(v)][c].append(nums[c][i])
    avg = {
        n: [stats.mean(cells[n][c]) if cells[n][c] else None for c in metrics]
        for n in names
    }
    notes = []
    if len(names) > 8:
        notes.append(f"Showing the first 8 of {len(names)} items.")
        names = names[:8]
    cols = list(zip(*[avg[n] for n in names]))
    lo = [min([v for v in col if v is not None] or [0]) for col in cols]
    hi = [max([v for v in col if v is not None] or [1]) for col in cols]
    norm = o.get("normalize", True)
    data = []
    for n in names:
        raw = avg[n]
        r = [
            (
                0
                if v is None
                else ((v - lo[j]) / (hi[j] - lo[j]) * 100 if hi[j] > lo[j] else 50)
            )
            if norm
            else (0 if v is None else v)
            for j, v in enumerate(raw)
        ]
        data.append(
            {
                "type": "scatterpolar",
                "name": n,
                "fill": "toself",
                "opacity": 0.6,
                "r": r + r[:1],
                "theta": metrics + metrics[:1],
                "customdata": [("n/a" if v is None else fmt_num(v)) for v in raw]
                + [fmt_num(raw[0]) if raw[0] is not None else "n/a"],
                "hovertemplate": "%{theta}: %{customdata}<extra>%{fullData.name}</extra>",
            }
        )
    layout = {
        "polar": {"radialaxis": {"visible": True, "range": [0, 100] if norm else None}},
        "showlegend": True,
    }
    if norm:
        notes.append(
            "Each metric is scaled to 0-100 (lowest item = 0, highest = 100) so different units can share one chart."
        )
    return fig(data, layout, notes)


def control_chart(t, m, o):
    xc, yc = m["x"][0], m["y"][0]
    xs, ys = t.values(xc), t.numbers(yc)
    rows = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if t.primary(xc) == "date":
        rows.sort(
            key=lambda r: (
                parse_date(r[0]) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)
            )
        )
    if len(rows) < 3:
        raise ChartError("A control chart needs at least 3 measurements.")
    vals = [r[1] for r in rows]
    k = float(o.get("sigma", 3))
    center = stats.mean(vals)
    mr = [abs(vals[i] - vals[i - 1]) for i in range(1, len(vals))]
    sigma = stats.mean(mr) / 1.128  # d2 constant for moving ranges of size 2
    ucl, lcl = center + k * sigma, center - k * sigma
    xl = [r[0] if t.primary(xc) != "text" else fmt_label(r[0]) for r in rows]
    out = [i for i, v in enumerate(vals) if v > ucl or v < lcl]
    data = [
        {
            "type": "scatter",
            "mode": "lines+markers",
            "x": xl,
            "y": vals,
            "name": yc,
            "marker": {"size": 6},
            "line": {"width": 1.5},
        },
        {
            "type": "scatter",
            "mode": "markers",
            "x": [xl[i] for i in out],
            "y": [vals[i] for i in out],
            "name": "Out of control",
            "marker": {
                "size": 12,
                "color": PALETTE[3],
                "symbol": "circle-open",
                "line": {"width": 3, "color": PALETTE[3]},
            },
        },
    ]
    for name, y, dash in (
        (f"UCL ({k:g}σ)", ucl, "dash"),
        ("Centre", center, "solid"),
        (f"LCL ({k:g}σ)", lcl, "dash"),
    ):
        data.append(
            {
                "type": "scatter",
                "mode": "lines",
                "x": [xl[0], xl[-1]],
                "y": [y, y],
                "name": name,
                "line": {"dash": dash, "width": 1.5, "color": "#999999"},
            }
        )
    notes = [
        (
            f"Centre {fmt_num(center)} · limits {fmt_num(lcl)} to {fmt_num(ucl)} (individuals chart, "
            f"σ estimated from moving ranges)."
        )
    ]
    notes.append(
        f"{len(out)} point(s) outside the control limits."
        if out
        else "No points outside the control limits."
    )
    return fig(data, {"xaxis": ax(xc), "yaxis": ax(yc), "showlegend": True}, notes)


def _finance(kind: str, t, m, o):
    xc = m["x"][0]
    cols = {k: t.numbers(m[k][0]) for k in ("open", "high", "low", "close")}
    xs = t.values(xc)
    rows = [
        i
        for i in range(len(t))
        if xs[i] is not None and all(c[i] is not None for c in cols.values())
    ]
    rows.sort(
        key=lambda i: (
            parse_date(xs[i]) or dt.datetime.min.replace(tzinfo=dt.timezone.utc)
        )
    )
    if not rows:
        raise ChartError("Need rows with a date and numeric open, high, low and close.")
    tr = {
        "type": kind,
        "x": [xs[i] for i in rows],
        "name": "Price",
        **{k: [c[i] for i in rows] for k, c in cols.items()},
        "increasing": {"line": {"color": PALETTE[0]}},
        "decreasing": {"line": {"color": PALETTE[1]}},
    }
    layout = {
        "xaxis": ax(xc, type="date", rangeslider={"visible": False}),
        "yaxis": ax("Price"),
        "showlegend": False,
    }
    return fig(
        [tr],
        layout,
        ["Blue = close above open (up), orange = close below open (down)."],
    )


def candlestick(t, m, o):
    return _finance("candlestick", t, m, o)


def ohlc(t, m, o):
    return _finance("ohlc", t, m, o)
