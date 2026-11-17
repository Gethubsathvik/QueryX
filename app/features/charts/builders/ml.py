"""Machine-learning charts: scree, ROC, precision-recall, confusion matrix, learning curve, decision tree."""
from __future__ import annotations

import html

from .. import stats
from ..errors import ChartError
from ..table import fmt_label
from ..tree import DecisionTree, looks_categorical
from .common import PALETTE, ax, fig, hex_rgba, numeric_frame, sort_labels

POSITIVE_WORDS = {"1", "true", "yes", "y", "positive", "pos", "fraud", "churn", "spam"}


def scree(t, m, o):
    cols = m["columns"]
    idx, data = numeric_frame(t, cols)
    if len(idx) < 3:
        raise ChartError("A scree plot needs at least 3 rows where every selected column is numeric.")
    keep = [c for c in cols if stats.stdev(data[c]) > 0]
    if len(keep) < 2:
        raise ChartError("Need at least 2 numeric columns that vary.")
    eig = [max(e, 0.0) for e in stats.jacobi_eigenvalues(stats.correlation_matrix([data[c] for c in keep]))]
    total = sum(eig)
    ratio = [e / total * 100 for e in eig]
    cum, run = [], 0.0
    for r in ratio:
        run += r
        cum.append(run)
    pcs = [f"PC{i + 1}" for i in range(len(eig))]
    traces = [{"type": "bar", "x": pcs, "y": ratio, "name": "Variance explained (%)", "customdata": eig,
               "hovertemplate": "%{x}: %{y:.1f}% (eigenvalue %{customdata:.2f})<extra></extra>"},
              {"type": "scatter", "mode": "lines+markers", "x": pcs, "y": cum, "name": "Cumulative (%)"}]
    layout = {"xaxis": ax("Principal component", type="category"), "yaxis": ax("Variance explained (%)", range=[0, 105]),
              "showlegend": True,
              "shapes": [{"type": "line", "x0": 0, "x1": 1, "xref": "paper", "y0": 100 / len(eig), "y1": 100 / len(eig),
                          "line": {"dash": "dot", "color": "#999999"}}],
              "annotations": [{"xref": "paper", "x": 1, "y": 100 / len(eig), "text": "Kaiser rule (eigenvalue = 1)",
                               "showarrow": False, "yanchor": "bottom", "xanchor": "right"}]}
    notes = [f"PCA on the standardised columns ({len(keep)} columns, {len(idx)} rows). "
             f"{sum(1 for e in eig if e > 1)} component(s) have eigenvalue above 1."]
    if len(keep) < len(cols):
        notes.append(f"Dropped constant columns: {', '.join(c for c in cols if c not in keep)}.")
    return fig(traces, layout, notes)


def _binary(t, m, o):
    """Return (positive-label, [bool], {score col: [float]}, kept row indexes, notes)."""
    actual = [fmt_label(v) if v is not None else None for v in t.values(m["actual"][0])]
    scores = {c: t.numbers(c) for c in m["score"]}
    rows = [i for i in range(len(t)) if actual[i] is not None and all(s[i] is not None for s in scores.values())]
    labels = sort_labels(actual[i] for i in rows)
    if len(labels) != 2:
        raise ChartError(f"'{m['actual'][0]}' must have exactly 2 distinct values (found {len(labels)}).")
    chosen = str(o.get("positive", "")).strip()
    if chosen in labels:
        pos = chosen
    else:
        pos = next((l for l in labels if l.lower() in POSITIVE_WORDS), labels[-1])
    notes = [f"Positive class: '{pos}' ({sum(1 for i in rows if actual[i] == pos)} of {len(rows)} rows)."]
    return pos, [actual[i] == pos for i in rows], {c: [s[i] for i in rows] for c, s in scores.items()}, notes


def roc(t, m, o):
    _, y, scores, notes = _binary(t, m, o)
    data = []
    for name, s in scores.items():
        fpr, tpr, auc = stats.roc_curve(y, s)
        data.append({"type": "scatter", "mode": "lines", "x": fpr, "y": tpr, "name": f"{name} (AUC {auc:.3f})"})
    data.append({"type": "scatter", "mode": "lines", "x": [0, 1], "y": [0, 1], "name": "Chance",
                 "line": {"dash": "dash", "color": "#999999"}})
    layout = {"xaxis": ax("False positive rate", range=[0, 1]),
              "yaxis": ax("True positive rate", range=[0, 1.02]),
              "showlegend": True, "legend": {"x": 0.98, "xanchor": "right", "y": 0.02}}
    return fig(data, layout, notes + ["AUC 0.5 = random guessing, 1.0 = perfect ranking."])


def pr(t, m, o):
    _, y, scores, notes = _binary(t, m, o)
    prevalence = sum(y) / len(y)
    data = []
    for name, s in scores.items():
        rec, prec, ap = stats.pr_curve(y, s)
        data.append({"type": "scatter", "mode": "lines", "x": rec, "y": prec, "name": f"{name} (AP {ap:.3f})",
                     "line": {"shape": "hv"}})
    data.append({"type": "scatter", "mode": "lines", "x": [0, 1], "y": [prevalence] * 2,
                 "name": f"No-skill ({prevalence:.2f})", "line": {"dash": "dash", "color": "#999999"}})
    layout = {"xaxis": ax("Recall", range=[0, 1]), "yaxis": ax("Precision", range=[0, 1.02]), "showlegend": True,
              "legend": {"x": 0.02, "xanchor": "left", "y": 0.02}}
    return fig(data, layout, notes + ["AP = average precision. The dashed line is a model that guesses at the class rate."])


def confusion_matrix(t, m, o):
    a, p = t.values(m["actual"][0]), t.values(m["predicted"][0])
    w = t.numbers(m["count"][0]) if m.get("count") else [1.0] * len(t)
    cell: dict[tuple[str, str], float] = {}
    for av, pv, wv in zip(a, p, w):
        if av is None or pv is None or wv is None:
            continue
        cell[(fmt_label(av), fmt_label(pv))] = cell.get((fmt_label(av), fmt_label(pv)), 0.0) + wv
    if not cell:
        raise ChartError("No rows with both an actual and a predicted value.")
    labels = sort_labels([k[0] for k in cell] + [k[1] for k in cell])
    if len(labels) > 25:
        raise ChartError("Too many classes for a confusion matrix (limit 25).")
    z = [[cell.get((r, c), 0.0) for c in labels] for r in labels]
    total = sum(sum(row) for row in z)
    diag = sum(z[i][i] for i in range(len(labels)))
    pct = o.get("normalize") == "row percent"
    shown = [[(v / sum(row) * 100 if sum(row) else 0.0) for v in row] for row in z] if pct else z
    tr = {"type": "heatmap", "x": labels, "y": labels, "z": shown, "colorscale": [[0, "#eef4fb"], [1, "#0072B2"]],
          "customdata": z, "texttemplate": "%{z:.1f}%" if pct else "%{z:,.0f}",
          "hovertemplate": "Actual %{y}, predicted %{x}<br>%{customdata:,.0f} rows<extra></extra>",
          "colorbar": {"title": {"text": "% of actual" if pct else "Count"}}}
    layout = {"xaxis": ax("Predicted", type="category", side="bottom"),
              "yaxis": ax("Actual", type="category", autorange="reversed")}
    return fig([tr], layout, [f"Accuracy {diag / total:.1%} ({diag:,.0f} of {total:,.0f}). The diagonal holds correct predictions."])


def learning_curve(t, m, o):
    xc = m["x"][0]
    xs = t.numbers(xc)
    data, notes = [], []
    for j, col in enumerate(m["y"]):
        ys = t.numbers(col)
        by: dict[float, list[float]] = {}
        for x, y in zip(xs, ys):
            if x is not None and y is not None:
                by.setdefault(x, []).append(y)
        if not by:
            continue
        keys = sorted(by)
        mu = [stats.mean(by[k]) for k in keys]
        sd = [stats.stdev(by[k]) for k in keys]
        color = PALETTE[j % len(PALETTE)]
        data.append({"type": "scatter", "mode": "lines", "x": keys, "y": [a + b for a, b in zip(mu, sd)],
                     "line": {"width": 0, "color": color}, "showlegend": False, "hoverinfo": "skip", "legendgroup": col})
        data.append({"type": "scatter", "mode": "lines", "x": keys, "y": [a - b for a, b in zip(mu, sd)],
                     "line": {"width": 0, "color": color}, "fill": "tonexty", "fillcolor": hex_rgba(color, 0.18),
                     "showlegend": False, "hoverinfo": "skip", "legendgroup": col})
        data.append({"type": "scatter", "mode": "lines+markers", "x": keys, "y": mu, "name": col,
                     "line": {"color": color}, "legendgroup": col})
        if any(len(v) > 1 for v in by.values()):
            notes = ["Line = mean across repeated runs/folds, shaded band = ±1 standard deviation."]
    if not data:
        raise ChartError("No numeric rows to plot.")
    return fig(data, {"xaxis": ax(xc), "yaxis": ax("Score"), "showlegend": True}, notes)


def decision_tree(t, m, o):
    target = m["target"][0]
    feats = [f for f in m["features"] if f != target]
    if not feats:
        raise ChartError("Pick at least one numeric feature that is different from the target.")
    tv, fcols = t.values(target), [t.numbers(f) for f in feats]
    rows = [i for i in range(len(t)) if tv[i] is not None and all(c[i] is not None for c in fcols)]
    if len(rows) < 10:
        raise ChartError("A decision tree needs at least 10 complete rows.")
    rows = rows[:2000]
    classify = looks_categorical([tv[i] for i in rows])
    if classify:
        y = [fmt_label(tv[i]) for i in rows]
        if len(set(y)) < 2:
            raise ChartError("The target has only one value, so there is nothing to predict.")
    else:
        y = [float(tv[i]) for i in rows]
    X = [[c[i] for c in fcols] for i in rows]
    tree = DecisionTree("classification" if classify else "regression", int(o.get("max_depth", 3)),
                        int(o.get("min_leaf", 5))).fit(X, y)

    pos, counter = {}, [0]

    def place(node):
        if node["feature"] is None:
            x = float(counter[0])
            counter[0] += 1
        else:
            x = (place(node["left"]) + place(node["right"])) / 2
        pos[id(node)] = (x, -float(node["depth"]))
        return x

    place(tree.root)
    leaves, depth = counter[0], tree.depth()
    ex, ey = [], []
    hx, hy, ht, ann = [], [], [], []
    for node in tree.nodes():
        x, yy = pos[id(node)]
        if node["feature"] is not None:
            for ch in (node["left"], node["right"]):
                cx, cy = pos[id(ch)]
                ex += [x, cx, None]
                ey += [yy, cy, None]
        leaf = node["feature"] is None
        if classify:
            k = node["prediction"]
            label = html.escape(str(tree.classes[k]))
            share = node["counts"][k] / node["n"]
            color = PALETTE[k % len(PALETTE)]
            detail = "<br>".join(f"{html.escape(str(c))}: {n}" for c, n in zip(tree.classes, node["counts"]))
            body = f"<b>{label}</b><br>{share:.0%} of n={node['n']}"
            hover = f"n = {node['n']}<br>gini = {node['impurity']:.3f}<br>{detail}"
        else:
            color = PALETTE[0]
            body = f"<b>mean {node['mean']:.4g}</b><br>n={node['n']}"
            hover = f"n = {node['n']}<br>mean = {node['mean']:.4g}<br>variance = {node['impurity']:.4g}"
        if not leaf:
            cond = f"{html.escape(feats[node['feature']])} ≤ {node['threshold']:.4g}"
            text = f"<b>{cond}</b><br>n={node['n']}"
            color = "#999999"
        else:
            text = body
        hx.append(x); hy.append(yy); ht.append(hover)
        ann.append({"x": x, "y": yy, "xref": "x", "yref": "y", "text": text, "showarrow": False, "align": "center",
                    "bgcolor": hex_rgba(color if color.startswith("#") else "#999999", 0.18),
                    "bordercolor": color, "borderwidth": 1.5, "borderpad": 5, "font": {"size": 12}})
    data = [{"type": "scatter", "mode": "lines", "x": ex, "y": ey, "hoverinfo": "skip",
             "line": {"color": "rgba(127,127,127,0.7)", "width": 1.5}, "showlegend": False},
            {"type": "scatter", "mode": "markers", "x": hx, "y": hy, "text": ht, "hoverinfo": "text",
             "marker": {"size": 44, "opacity": 0.01}, "showlegend": False}]
    layout = {"xaxis": {"visible": False, "range": [-0.7, leaves - 0.3]},
              "yaxis": {"visible": False, "range": [-depth - 0.55, 0.55]},
              "annotations": ann, "showlegend": False,
              "width": max(720, leaves * 150), "height": (depth + 1) * 125 + 70}
    score = tree.score(X, y)
    imp = sorted(zip(feats, tree.importances()), key=lambda kv: -kv[1])
    imp_txt = ", ".join(f"{f} {v:.0%}" for f, v in imp if v > 0) or "no split was useful"
    notes = [f"{'Classification' if classify else 'Regression'} tree · depth {depth} · {leaves} leaves · "
             f"{'accuracy' if classify else 'R²'} {score:.1%}" if classify else
             f"Regression tree · depth {depth} · {leaves} leaves · R² {score:.2f} (on the rows used to build it).",
             f"Feature importance: {imp_txt}.",
             "Follow the left branch when the condition is true (value ≤ threshold), the right branch otherwise."]
    if classify:
        notes[0] += " (on the rows used to build it)."
    return fig(data, layout, notes)
