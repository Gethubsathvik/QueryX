"""Compare and trend charts: bar family, line, area, time series, pie, doughnut."""
from __future__ import annotations

from ..errors import ChartError
from ..table import Table, fmt_label
from .common import ax, aggregate, fig, fmt_num, pivot


def _bar(t: Table, m: dict, o: dict, orientation: str, mode: str) -> dict:
    group = m.get("group", [])
    xs, series = pivot(t, m["x"][0], m["y"], group, o.get("agg", "sum"))
    notes = []
    if group and len(m["y"]) > 1:
        notes.append(f"Several value columns were selected; using '{m['y'][0]}' with the group column.")
    data = []
    for name, vals in series:
        tr = {"type": "bar", "name": name}
        tr.update({"x": vals, "y": xs, "orientation": "h"} if orientation == "h" else {"x": xs, "y": vals})
        data.append(tr)
    vtitle = m["y"][0] if (group or len(series) == 1) else "Value"
    cat = {"type": "category"} if t.primary(m["x"][0]) == "text" else {}
    layout = {"barmode": mode, "showlegend": len(series) > 1}
    if orientation == "h":
        layout["yaxis"] = ax(m["x"][0], autorange="reversed", **cat)
        layout["xaxis"] = ax(vtitle)
    else:
        layout["xaxis"] = ax(m["x"][0], **cat)
        layout["yaxis"] = ax(vtitle)
    return fig(data, layout, notes)


def bar(t, m, o):
    return _bar(t, m, o, "v", "group")


def hbar(t, m, o):
    return _bar(t, m, o, "h", "group")


def grouped_bar(t, m, o):
    return _bar(t, m, o, "v", "group")


def stacked_bar(t, m, o):
    return _bar(t, m, o, "v", "stack")


def _lines(t, m, o, how, fill=None, stacked=False):
    group = m.get("group", [])
    xs, series = pivot(t, m["x"][0], m["y"], group, how)
    data = []
    for name, vals in series:
        tr = {"type": "scatter", "name": name, "x": xs, "y": vals,
              "mode": "lines+markers" if len(xs) <= 60 else "lines"}
        if fill == "stack":
            tr.update(mode="lines", stackgroup="one")
        elif fill:
            tr["fill"] = fill
        data.append(tr)
    vtitle = m["y"][0] if (group or len(series) == 1) else "Value"
    layout = {"xaxis": ax(m["x"][0]), "yaxis": ax(vtitle), "showlegend": len(series) > 1, "hovermode": "x unified"}
    notes = []
    if group and len(m["y"]) > 1:
        notes.append(f"Several value columns were selected; using '{m['y'][0]}' with the group column.")
    return fig(data, layout, notes)


def line(t, m, o):
    return _lines(t, m, o, "sum")


def area(t, m, o):
    series_count = len(m["y"]) if not m.get("group") else max(2, 1)
    stacked = bool(o.get("stacked", True)) and (bool(m.get("group")) or len(m["y"]) > 1)
    return _lines(t, m, o, "sum", fill="stack" if stacked else "tozeroy")


def time_series(t, m, o):
    f = _lines(t, m, o, "mean")
    f["layout"]["xaxis"] = ax(m["x"][0], type="date", rangeslider={"visible": True}, rangeselector={
        "bgcolor": "rgba(127,127,127,0.15)",
        "buttons": [{"count": 1, "label": "1m", "step": "month", "stepmode": "backward"},
                    {"count": 3, "label": "3m", "step": "month", "stepmode": "backward"},
                    {"count": 6, "label": "6m", "step": "month", "stepmode": "backward"},
                    {"step": "all", "label": "All"}]})
    for tr in f["data"]:
        tr["mode"] = "lines"
    f["notes"].append("Repeated dates are averaged. Use the range buttons or drag the slider to zoom.")
    return f


def _pie(t: Table, m: dict, o: dict, hole: float) -> dict:
    labels, nums, how = t.values(m["label"][0]), t.numbers(m["value"][0]), o.get("agg", "sum")
    cells: dict[str, list] = {}
    for lab, v in zip(labels, nums):
        cells.setdefault(fmt_label(lab), []).append(v)
    items = [(k, aggregate(v, how)) for k, v in cells.items()]
    pos = sorted(((k, v) for k, v in items if v is not None and v > 0), key=lambda kv: -kv[1])
    notes = []
    if len(pos) < len(items):
        notes.append(f"{len(items) - len(pos)} slice(s) with zero, negative or missing values were left out.")
    if not pos:
        raise ChartError("Pie and doughnut charts need positive values.")
    if len(pos) > 12:
        rest = sum(v for _, v in pos[11:])
        notes.append(f"Showing the 11 largest of {len(pos)} slices; the rest are grouped as 'Other'.")
        pos = pos[:11] + [("Other", rest)]
    total = sum(v for _, v in pos)
    data = [{"type": "pie", "labels": [k for k, _ in pos], "values": [v for _, v in pos], "hole": hole,
             "sort": False, "textinfo": "label+percent", "textposition": "inside" if hole else "auto",
             "marker": {"line": {"color": "rgba(127,127,127,0.35)", "width": 1}}}]
    layout = {"showlegend": True}
    if hole:
        layout["annotations"] = [{"text": f"<b>{fmt_num(total)}</b><br>total", "showarrow": False,
                                  "font": {"size": 15}, "x": 0.5, "y": 0.5, "xref": "paper", "yref": "paper"}]
    return fig(data, layout, notes)


def pie(t, m, o):
    return _pie(t, m, o, 0.0)


def doughnut(t, m, o):
    return _pie(t, m, o, 0.5)
