"""Chart builders: one function per chart id, each returning a Plotly figure dict."""
from __future__ import annotations

from ..errors import ChartError
from ..table import Table
from . import basic, composition, distribution, ml, performance, relationship
from .common import PALETTE, clean

REGISTRY = {
    "bar": basic.bar, "hbar": basic.hbar, "grouped_bar": basic.grouped_bar, "stacked_bar": basic.stacked_bar,
    "line": basic.line, "area": basic.area, "time_series": basic.time_series, "pie": basic.pie,
    "doughnut": basic.doughnut,
    "histogram": distribution.histogram, "box": distribution.box, "violin": distribution.violin,
    "density": distribution.density, "qq": distribution.qq, "error_bar": distribution.error_bar,
    "rug": distribution.rug,
    "scatter": relationship.scatter, "bubble": relationship.bubble, "heatmap": relationship.heatmap,
    "correlation_matrix": relationship.correlation_matrix, "scatter3d": relationship.scatter3d,
    "surface3d": relationship.surface3d,
    "treemap": composition.treemap, "sunburst": composition.sunburst, "marimekko": composition.marimekko,
    "funnel": composition.funnel, "waterfall": composition.waterfall, "sankey": composition.sankey,
    "gantt": performance.gantt, "bullet": performance.bullet, "radar": performance.radar,
    "control_chart": performance.control_chart, "candlestick": performance.candlestick, "ohlc": performance.ohlc,
    "scree": ml.scree, "roc": ml.roc, "pr": ml.pr, "confusion_matrix": ml.confusion_matrix,
    "learning_curve": ml.learning_curve, "decision_tree": ml.decision_tree,
}


def build(chart_id: str, table: Table, mapping: dict, options: dict) -> dict:
    try:
        fn = REGISTRY[chart_id]
    except KeyError:
        raise ChartError(f"Unknown chart type '{chart_id}'.") from None
    return clean(fn(table, mapping, options))
