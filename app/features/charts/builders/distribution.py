"""Distribution charts: histogram, box, violin, density, Q-Q, error bar, rug."""
from __future__ import annotations

import math

from .. import stats
from ..errors import ChartError
from ..table import Table, fmt_label
from .common import MAX_GROUPS, ax, fig, fmt_num, group_positions, numeric_frame, x_order


def _values(t: Table, col: str, minimum: int = 2) -> list[float]:
    vals = [v for v in t.numbers(col) if v is not None]
    if len(vals) < minimum:
        raise ChartError(f"'{col}' needs at least {minimum} numeric values (found {len(vals)}).")
    return vals


def _series(t: Table, m: dict) -> tuple[list[tuple[str, list[float]]], list[str]]:
    """(name, values) per group, or per value column when there is no group."""
    notes, out = [], []
    group = m.get("group", [])
    if group:
        g, y = t.values(group[0]), t.numbers(m["y"][0])
        cells: dict[str, list[float]] = {}
        for gv, yv in zip(g, y):
            if yv is not None:
                cells.setdefault(fmt_label(gv), []).append(yv)
        if len(cells) > MAX_GROUPS:
            raise ChartError(f"'{group[0]}' has {len(cells)} distinct values; pick a column with at most {MAX_GROUPS}.")
        out = list(cells.items())
        if len(m["y"]) > 1:
            notes.append(f"Several value columns were selected; using '{m['y'][0]}' with the group column.")
    else:
        for col in m["y"]:
            vals = [v for v in t.numbers(col) if v is not None]
            if vals:
                out.append((col, vals))
    if not out:
        raise ChartError("No numeric values to plot.")
    return out, notes


def histogram(t, m, o):
    vals = _values(t, m["x"][0])
    tr = {"type": "histogram", "x": vals, "marker": {"line": {"width": 1, "color": "rgba(127,127,127,0.5)"}}}
    if o.get("bins"):
        tr["nbinsx"] = int(o["bins"])
    if o.get("norm"):
        tr["histnorm"] = o["norm"]
    mu = stats.mean(vals)
    layout = {"xaxis": ax(m["x"][0]), "yaxis": ax(o.get("norm") or "Count"), "bargap": 0.03, "showlegend": False,
              "shapes": [{"type": "line", "x0": mu, "x1": mu, "y0": 0, "y1": 1, "yref": "paper",
                          "line": {"dash": "dash", "width": 2, "color": "#D55E00"}}],
              "annotations": [{"x": mu, "y": 1, "yref": "paper", "text": f"mean {fmt_num(mu)}", "showarrow": False,
                               "yanchor": "bottom", "font": {"color": "#D55E00"}}]}
    s = sorted(vals)
    notes = [f"n = {len(vals)} · mean {fmt_num(mu)} · median {fmt_num(stats.quantile(s, 0.5))} · "
             f"std dev {fmt_num(stats.stdev(vals))}"]
    return fig([tr], layout, notes)


def box(t, m, o):
    series, notes = _series(t, m)
    data = [{"type": "box", "y": v, "name": n, "boxmean": True, "boxpoints": "outliers"} for n, v in series]
    return fig(data, {"yaxis": ax(m["y"][0] if len(series) > 1 or m.get("group") else "Value"), "showlegend": False},
               notes + ["Box = middle 50% of values, line = median, dashed line = mean, dots = outliers."])


def violin(t, m, o):
    series, notes = _series(t, m)
    skipped = [n for n, v in series if len(v) < 2]
    series = [(n, v) for n, v in series if len(v) >= 2]
    if not series:
        raise ChartError("Violin plots need at least 2 values per group.")
    if skipped:
        notes.append(f"Skipped groups with a single value: {', '.join(skipped[:5])}.")
    data = [{"type": "violin", "y": v, "name": n, "box": {"visible": True}, "meanline": {"visible": True},
             "points": False} for n, v in series]
    return fig(data, {"yaxis": ax(m["y"][0] if len(series) > 1 or m.get("group") else "Value"), "showlegend": False},
               notes)


def density(t, m, o):
    col = m["x"][0]
    x, g = t.numbers(col), (t.values(m["group"][0]) if m.get("group") else None)
    cells: dict[str, list[float]] = {}
    for i, v in enumerate(x):
        if v is not None:
            cells.setdefault(fmt_label(g[i]) if g else col, []).append(v)
    if len(cells) > MAX_GROUPS:
        raise ChartError("Too many groups for a density plot.")
    data, notes = [], []
    for name, vals in cells.items():
        if len(vals) < 2:
            notes.append(f"Skipped '{name}': needs at least 2 values.")
            continue
        gx, gy = stats.gaussian_kde(vals)
        data.append({"type": "scatter", "mode": "lines", "x": gx, "y": gy, "name": name, "fill": "tozeroy",
                     "opacity": 0.8 if len(cells) == 1 else 0.55})
    if not data:
        raise ChartError("Density plots need at least 2 numeric values.")
    notes.append("Gaussian kernel density estimate (Silverman bandwidth); the area under each curve is 1.")
    return fig(data, {"xaxis": ax(col), "yaxis": ax("Density"), "showlegend": len(data) > 1}, notes)


def qq(t, m, o):
    col = m["y"][0]
    vals = sorted(_values(t, col, 3))
    n = len(vals)
    theo = [stats.normal_ppf((i + 0.5) / n) for i in range(n)]
    q1, q3 = stats.quantile(vals, 0.25), stats.quantile(vals, 0.75)
    z1, z3 = stats.normal_ppf(0.25), stats.normal_ppf(0.75)
    slope = (q3 - q1) / (z3 - z1) if q3 > q1 else 0.0
    icpt = q1 - slope * z1
    data = [{"type": "scatter", "mode": "markers", "x": theo, "y": vals, "name": "Data", "marker": {"size": 6}},
            {"type": "scatter", "mode": "lines", "x": [theo[0], theo[-1]],
             "y": [icpt + slope * theo[0], icpt + slope * theo[-1]], "name": "Normal reference",
             "line": {"dash": "dash"}}]
    r = stats.pearson(theo, vals)
    notes = ["Points close to the dashed line mean the data is roughly normally distributed."]
    if r is not None:
        notes.insert(0, f"Correlation with normal quantiles: {r:.3f} (n = {n}).")
    return fig(data, {"xaxis": ax("Theoretical quantiles (standard normal)"), "yaxis": ax(f"Sample quantiles of {col}"),
                      "showlegend": True}, notes)


def error_bar(t, m, o):
    xcol, ycol = m["x"][0], m["y"][0]
    ecol = m["error"][0] if m.get("error") else None
    xs, ys = t.values(xcol), t.numbers(ycol)
    es = t.numbers(ecol) if ecol else None
    keys = x_order(t, xcol, list(dict.fromkeys(xs)))
    if len(keys) > 60:
        raise ChartError(f"'{xcol}' has {len(keys)} distinct values; group in SQL first (limit 60).")
    labels, means, errs = [], [], []
    for k in keys:
        ids = [i for i, v in enumerate(xs) if v == k and ys[i] is not None]
        if not ids:
            continue
        vals = [ys[i] for i in ids]
        labels.append(fmt_label(k))
        means.append(stats.mean(vals))
        if es:
            ev = [es[i] for i in ids if es[i] is not None]
            errs.append(stats.mean(ev) if ev else 0.0)
        else:
            errs.append(1.96 * stats.stdev(vals) / math.sqrt(len(vals)) if len(vals) > 1 else 0.0)
    if not labels:
        raise ChartError("No numeric values to plot.")
    data = [{"type": "scatter", "mode": "markers", "x": labels, "y": means, "name": f"Mean of {ycol}",
             "marker": {"size": 10}, "error_y": {"type": "data", "array": errs, "visible": True, "thickness": 2,
                                                 "width": 6}}]
    note = (f"Error bars come from '{ecol}'." if ecol else
            "Error bars show the 95% confidence interval of the mean (1.96 x standard error); "
            "categories with a single value have no interval.")
    return fig(data, {"xaxis": ax(xcol, type="category"), "yaxis": ax(f"Mean of {ycol}"), "showlegend": False}, [note])


def rug(t, m, o):
    col = m["x"][0]
    vals = _values(t, col)
    data = [{"type": "histogram", "x": vals, "name": "Histogram", "yaxis": "y", "opacity": 0.85,
             "marker": {"line": {"width": 1, "color": "rgba(127,127,127,0.5)"}}},
            {"type": "scatter", "mode": "markers", "x": vals, "y": ["rug"] * len(vals), "name": "Observations",
             "yaxis": "y2", "marker": {"symbol": "line-ns-open", "size": 14, "line": {"width": 1.2},
                                       "color": "#D55E00"},
             "hovertemplate": col + ": %{x}<extra></extra>"}]
    layout = {"xaxis": ax(col, anchor="y2"), "yaxis": {"domain": [0.22, 1], "title": {"text": "Count"}},
              "yaxis2": {"domain": [0, 0.15], "visible": False}, "showlegend": False, "bargap": 0.03}
    return fig(data, layout, [f"n = {len(vals)}. Each tick below the histogram is one observation."])
