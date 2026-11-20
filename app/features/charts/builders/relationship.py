"""Relationship charts: scatter, bubble, heatmap, correlation matrix, 3D scatter, 3D surface."""

from __future__ import annotations

from .. import stats
from ..errors import ChartError
from ..table import Table, fmt_label
from .common import ax, fig, grid, group_positions, numeric_frame, tick_subset


def _hover_text(t: Table, m: dict, idx: list[int]):
    if m.get("label"):
        v = t.values(m["label"][0])
        return [fmt_label(v[i]) for i in idx]
    return None


def scatter(t, m, o):
    x, y = m["x"][0], m["y"][0]
    idx, cols = numeric_frame(t, [x, y])
    if len(idx) < 2:
        raise ChartError("A scatter plot needs at least 2 rows with numeric X and Y.")
    groups = group_positions(t, m.get("group", []), idx)
    text = _hover_text(t, m, idx)
    data = []
    for name, pos in groups.items():
        tr = {
            "type": "scatter",
            "mode": "markers",
            "name": name or f"{y} vs {x}",
            "x": [cols[x][p] for p in pos],
            "y": [cols[y][p] for p in pos],
            "marker": {"size": 8, "opacity": 0.75},
        }
        if text:
            tr["text"] = [text[p] for p in pos]
        data.append(tr)
    notes = []
    r = stats.pearson(cols[x], cols[y])
    if r is not None:
        notes.append(f"Pearson correlation r = {r:.3f} over {len(idx)} points.")
    fit = stats.ols(cols[x], cols[y]) if o.get("trendline", True) else None
    if fit:
        slope, icpt, r2 = fit
        lo, hi = min(cols[x]), max(cols[x])
        data.append(
            {
                "type": "scatter",
                "mode": "lines",
                "x": [lo, hi],
                "y": [icpt + slope * lo, icpt + slope * hi],
                "name": f"Trend (R² = {r2:.2f})",
                "line": {"dash": "dash", "color": "#999999"},
            }
        )
    return fig(
        data, {"xaxis": ax(x), "yaxis": ax(y), "showlegend": len(data) > 1}, notes
    )


def bubble(t, m, o):
    x, y, s = m["x"][0], m["y"][0], m["size"][0]
    idx, cols = numeric_frame(t, [x, y, s])
    if len(idx) < 2:
        raise ChartError(
            "A bubble chart needs at least 2 rows with numeric X, Y and size."
        )
    sizes = [max(v, 0.0) for v in cols[s]]
    biggest = max(sizes) or 1.0
    groups = group_positions(t, m.get("group", []), idx)
    text = _hover_text(t, m, idx)
    data = []
    for name, pos in groups.items():
        tr = {
            "type": "scatter",
            "mode": "markers",
            "name": name or s,
            "x": [cols[x][p] for p in pos],
            "y": [cols[y][p] for p in pos],
            "marker": {
                "size": [sizes[p] for p in pos],
                "sizemode": "area",
                "sizeref": 2 * biggest / 45**2,
                "sizemin": 3,
                "opacity": 0.7,
                "line": {"width": 1, "color": "rgba(127,127,127,0.6)"},
            },
            "customdata": [cols[s][p] for p in pos],
            "hovertemplate": f"{x}: %{{x}}<br>{y}: %{{y}}<br>{s}: %{{customdata}}"
            + ("<br>%{text}" if text else "")
            + "<extra>%{fullData.name}</extra>",
        }
        if text:
            tr["text"] = [text[p] for p in pos]
        data.append(tr)
    return fig(
        data,
        {"xaxis": ax(x), "yaxis": ax(y), "showlegend": len(data) > 1},
        [f"Bubble area is proportional to '{s}'."],
    )


def heatmap(t, m, o):
    xl, yl, z = grid(t, m["x"][0], m["y"][0], m["value"][0], o.get("agg", "sum"))
    flat = [v for row in z for v in row if v is not None]
    if not flat:
        raise ChartError("The value column has no numbers to colour the heatmap.")
    tr = {
        "type": "heatmap",
        "x": xl,
        "y": yl,
        "z": z,
        "colorscale": "Viridis",
        "hoverongaps": False,
        "colorbar": {"title": {"text": m["value"][0]}},
    }
    if len(xl) * len(yl) <= 150:
        tr["texttemplate"] = (
            "%{z:,.0f}" if max(abs(v) for v in flat) >= 100 else "%{z:.2f}"
        )
    layout = {
        "xaxis": ax(m["x"][0], type="category"),
        "yaxis": ax(m["y"][0], type="category", autorange="reversed"),
    }
    return fig([tr], layout, [])


def correlation_matrix(t, m, o):
    cols = m["columns"]
    idx, data = numeric_frame(t, cols)
    notes = []
    if len(idx) < 3:
        raise ChartError(
            "A correlation matrix needs at least 3 rows where every selected column is numeric."
        )
    keep = [c for c in cols if stats.stdev(data[c]) > 0]
    if len(keep) < len(cols):
        notes.append(
            f"Dropped constant columns: {', '.join(c for c in cols if c not in keep)}."
        )
    if len(keep) < 2:
        raise ChartError("Need at least 2 numeric columns that vary.")
    z = stats.correlation_matrix([data[c] for c in keep])
    tr = {
        "type": "heatmap",
        "x": keep,
        "y": keep,
        "z": z,
        "zmin": -1,
        "zmax": 1,
        "colorscale": "RdBu",
        "reversescale": True,
        "texttemplate": "%{z:.2f}",
        "colorbar": {"title": {"text": "r"}},
    }
    notes.append(
        f"Pearson correlation using {len(idx)} rows where all columns are present."
    )
    return fig(
        [tr],
        {
            "xaxis": ax(None, type="category"),
            "yaxis": ax(None, type="category", autorange="reversed"),
        },
        notes,
    )


def scatter3d(t, m, o):
    x, y, z = m["x"][0], m["y"][0], m["z"][0]
    idx, cols = numeric_frame(t, [x, y, z])
    if len(idx) < 2:
        raise ChartError(
            "A 3D scatter plot needs at least 2 rows with numeric X, Y and Z."
        )
    groups = group_positions(t, m.get("group", []), idx)
    data = [
        {
            "type": "scatter3d",
            "mode": "markers",
            "name": name or "points",
            "x": [cols[x][p] for p in pos],
            "y": [cols[y][p] for p in pos],
            "z": [cols[z][p] for p in pos],
            "marker": {"size": 4, "opacity": 0.8},
        }
        for name, pos in groups.items()
    ]
    layout = {
        "scene": {"xaxis": ax(x), "yaxis": ax(y), "zaxis": ax(z)},
        "showlegend": len(data) > 1,
        "margin": {"l": 0, "r": 0, "t": 10, "b": 0},
    }
    return fig(data, layout, ["Drag to rotate, scroll to zoom."])


def surface3d(t, m, o):
    xl, yl, z = grid(t, m["x"][0], m["y"][0], m["z"][0], o.get("agg", "sum"))
    if len(xl) < 2 or len(yl) < 2:
        raise ChartError(
            "A surface needs at least 2 distinct values on each of X and Y."
        )
    xi, yi = tick_subset(len(xl)), tick_subset(len(yl))
    tr = {
        "type": "surface",
        "x": list(range(len(xl))),
        "y": list(range(len(yl))),
        "z": z,
        "colorscale": "Viridis",
        "colorbar": {"title": {"text": m["z"][0]}},
    }
    layout = {
        "scene": {
            "xaxis": ax(m["x"][0], tickvals=xi, ticktext=[xl[i] for i in xi]),
            "yaxis": ax(m["y"][0], tickvals=yi, ticktext=[yl[i] for i in yi]),
            "zaxis": ax(m["z"][0]),
        },
        "margin": {"l": 0, "r": 0, "t": 10, "b": 0},
    }
    missing = sum(1 for row in z for v in row if v is None)
    notes = ["Drag to rotate, scroll to zoom."]
    if missing:
        notes.append(f"{missing} grid cell(s) have no data and are left as gaps.")
    return fig([tr], layout, notes)
