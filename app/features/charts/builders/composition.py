"""Part-to-whole and flow charts: treemap, sunburst, Marimekko, funnel, waterfall, Sankey."""
from __future__ import annotations

from ..errors import ChartError
from ..table import fmt_label
from .common import PALETTE, ax, fig, fmt_num, x_order


def _hierarchy(t, m):
    path, vcol = m["path"], m["value"][0]
    labels = [t.values(c) for c in path]
    nums = t.numbers(vcol)
    totals: dict[tuple, float] = {}
    dropped = 0
    for i, v in enumerate(nums):
        if v is None or v <= 0:
            dropped += 1
            continue
        key = tuple(fmt_label(col[i]) for col in labels)
        for d in range(1, len(key) + 1):
            totals[key[:d]] = totals.get(key[:d], 0.0) + v
    if not totals:
        raise ChartError("Treemaps and sunbursts need positive values.")
    if len(totals) > 3000:
        raise ChartError("Too many nodes to draw; aggregate in SQL first.")
    ids = [" / ".join(k) for k in totals]
    parents = [" / ".join(k[:-1]) for k in totals]
    return {"ids": ids, "labels": [k[-1] for k in totals], "parents": parents, "values": list(totals.values()),
            "branchvalues": "total", "hovertemplate": "%{label}<br>%{value:,.0f} (%{percentParent:.1%} of parent)"
                                                       "<extra></extra>"}, dropped


def treemap(t, m, o):
    tr, dropped = _hierarchy(t, m)
    tr.update(type="treemap", textinfo="label+value", marker={"line": {"width": 1}})
    return fig([tr], {"margin": {"l": 8, "r": 8, "t": 8, "b": 8}},
               [f"{dropped} row(s) with zero or missing size were left out."] if dropped else [])


def sunburst(t, m, o):
    tr, dropped = _hierarchy(t, m)
    tr.update(type="sunburst", insidetextorientation="radial")
    return fig([tr], {"margin": {"l": 8, "r": 8, "t": 8, "b": 8}},
               [f"{dropped} row(s) with zero or missing size were left out."] if dropped else [])


def marimekko(t, m, o):
    xc, gc, vc = m["x"][0], m["group"][0], m["value"][0]
    xv, gv, nv = t.values(xc), t.values(gc), t.numbers(vc)
    xkeys = x_order(t, xc, list(dict.fromkeys(xv)))
    gnames = list(dict.fromkeys(fmt_label(v) for v in gv))
    if len(gnames) > 15 or len(xkeys) > 40:
        raise ChartError("Marimekko charts work best with at most 40 columns and 15 segments; aggregate in SQL first.")
    cell: dict = {}
    for a, b, v in zip(xv, gv, nv):
        if v is not None and v > 0:
            cell[(a, fmt_label(b))] = cell.get((a, fmt_label(b)), 0.0) + v
    totals = {k: sum(cell.get((k, g), 0.0) for g in gnames) for k in xkeys}
    xkeys = [k for k in xkeys if totals[k] > 0]
    if not xkeys:
        raise ChartError("Marimekko charts need positive values.")
    grand = sum(totals[k] for k in xkeys)
    centers, cum = [], 0.0
    for k in xkeys:
        centers.append(cum + totals[k] / 2)
        cum += totals[k]
    labels = [fmt_label(k) for k in xkeys]
    data = []
    for g in gnames:
        vals = [cell.get((k, g), 0.0) for k in xkeys]
        data.append({"type": "bar", "name": g, "x": centers, "width": [totals[k] for k in xkeys],
                     "y": [v / totals[k] * 100 for v, k in zip(vals, xkeys)], "customdata": vals, "text": labels,
                     "textposition": "none", "marker": {"line": {"width": 1.5, "color": "rgba(127,127,127,0.6)"}},
                     "hovertemplate": "<b>%{text}</b><br>%{fullData.name}: %{y:.1f}% (%{customdata:,.0f})"
                                      "<extra></extra>"})
    layout = {"barmode": "stack", "xaxis": ax(f"{xc} (column width = total {vc})", tickvals=centers, ticktext=labels,
                                              range=[0, grand]),
              "yaxis": ax(f"Share of {xc} (%)", range=[0, 100], ticksuffix="%")}
    return fig(data, layout, [])


def funnel(t, m, o):
    st, vals = t.values(m["stage"][0]), t.numbers(m["value"][0])
    rows = [(fmt_label(s), v) for s, v in zip(st, vals) if v is not None]
    if not rows:
        raise ChartError("The funnel needs numeric counts.")
    data = [{"type": "funnel", "y": [r[0] for r in rows], "x": [r[1] for r in rows],
             "textinfo": "value+percent initial+percent previous"}]
    return fig(data, {"yaxis": ax(None, type="category")},
               ["Stages are drawn in the order of your rows; sort them in SQL to change the order."])


def waterfall(t, m, o):
    xs, ys = t.values(m["x"][0]), t.numbers(m["y"][0])
    rows = [(fmt_label(a), v) for a, v in zip(xs, ys) if v is not None]
    if not rows:
        raise ChartError("The waterfall needs numeric changes.")
    if len(rows) > 60:
        raise ChartError("Too many steps for a waterfall (limit 60).")
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    measure = ["relative"] * len(rows)
    if o.get("total", True):
        labels.append("Total")
        vals.append(sum(vals))
        measure.append("total")
    data = [{"type": "waterfall", "x": labels, "y": vals, "measure": measure,
             "text": [f"{v:+,.0f}" if k == "relative" else f"{v:,.0f}" for v, k in zip(vals, measure)],
             "textposition": "outside",
             "increasing": {"marker": {"color": PALETTE[2]}}, "decreasing": {"marker": {"color": PALETTE[3]}},
             "totals": {"marker": {"color": PALETTE[0]}}, "connector": {"line": {"color": "rgba(127,127,127,0.6)"}}}]
    return fig(data, {"xaxis": ax(m["x"][0], type="category"), "yaxis": ax(m["y"][0]), "showlegend": False}, [])


def sankey(t, m, o):
    src, tgt, val = t.values(m["source"][0]), t.values(m["target"][0]), t.numbers(m["value"][0])
    links: dict[tuple[str, str], float] = {}
    skipped = 0
    for a, b, v in zip(src, tgt, val):
        a, b = fmt_label(a), fmt_label(b)
        if v is None or v <= 0 or a == b:
            skipped += 1
            continue
        links[(a, b)] = links.get((a, b), 0.0) + v
    if not links:
        raise ChartError("The Sankey diagram needs positive flows between different nodes.")
    nodes: list[str] = []
    for a, b in links:
        for n in (a, b):
            if n not in nodes:
                nodes.append(n)
    if len(nodes) > 120:
        raise ChartError("Too many nodes for a Sankey diagram (limit 120).")
    # Sankey cannot draw loops: check the flow graph is acyclic (Kahn's algorithm).
    indeg = {n: 0 for n in nodes}
    for _, b in links:
        indeg[b] += 1
    queue, seen = [n for n in nodes if indeg[n] == 0], 0
    while queue:
        n = queue.pop()
        seen += 1
        for (a, b) in links:
            if a == n:
                indeg[b] -= 1
                if indeg[b] == 0:
                    queue.append(b)
    if seen < len(nodes):
        raise ChartError("These flows loop back on themselves; a Sankey diagram needs flows that only go forward.")
    pos = {n: i for i, n in enumerate(nodes)}
    data = [{"type": "sankey", "arrangement": "snap",
             "node": {"label": nodes, "pad": 14, "thickness": 16,
                      "color": [PALETTE[i % len(PALETTE)] for i in range(len(nodes))]},
             "link": {"source": [pos[a] for a, _ in links], "target": [pos[b] for _, b in links],
                      "value": list(links.values()), "color": "rgba(127,127,127,0.35)"}}]
    return fig(data, {"margin": {"l": 10, "r": 10, "t": 10, "b": 10}},
               [f"{skipped} row(s) were skipped (zero, missing, or from a node to itself)."] if skipped else [])
