import json

import pytest

from app.features.charts import stats
from app.features.charts.catalog import BY_ID, CATALOG
from app.features.charts.errors import ChartError
from app.features.charts.mapping import parse_options, resolve
from app.features.charts.service import ChartService, suggest_chart
from app.features.charts.table import Table
from app.features.charts.tree import DecisionTree
from app.features.data.repository import Database
from app.features.data.service import DataService

REQUESTED = [
    "Bar Chart",
    "Line Chart",
    "Pie Chart",
    "Histogram",
    "Area Chart",
    "Scatter Plot",
    "Horizontal Bar Chart",
    "Doughnut Chart",
    "Box Plot",
    "Violin Plot",
    "Density Plot",
    "Q-Q Plot",
    "Error Bar Chart",
    "Rug Plot",
    "Stacked Bar Chart",
    "Grouped Bar Chart",
    "Bubble Chart",
    "Heatmap",
    "Correlation Matrix",
    "Treemap",
    "Waterfall Chart",
    "Funnel Chart",
    "Radar Chart",
    "Sunburst Chart",
    "Sankey Diagram",
    "Gantt Chart",
    "Bullet Chart",
    "Marimekko Chart",
    "Time-Series Chart",
    "Candlestick Chart",
    "OHLC Chart",
    "Control Chart",
    "3D Surface Plot",
    "3D Scatter Plot",
    "Scree Plot",
    "ROC Curve",
    "Precision-Recall Curve",
    "Confusion Matrix",
    "Learning Curve",
    "Decision Tree",
]


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    db = Database(tmp_path_factory.mktemp("charts") / "a.db")
    db.ensure_seeded()
    return DataService(db, 500, 5)


def test_catalog_has_every_requested_chart_exactly_once():
    labels = [c.label.lower().replace("-", " ") for c in CATALOG]
    assert len(CATALOG) == len(REQUESTED) == 40 == len(BY_ID)
    for name in REQUESTED:
        wanted = (
            name.lower()
            .replace("-", " ")
            .replace(" chart", "")
            .replace(" plot", "")
            .replace(" diagram", "")
        )
        wanted = wanted.replace(" curve", "")
        assert any(wanted in l for l in labels), name


@pytest.mark.parametrize("spec", CATALOG, ids=lambda s: s.id)
def test_every_example_query_draws_its_chart(spec, data):
    r = data.execute(spec.example_sql)
    out = ChartService().build(r["columns"], r["rows"], spec.id)
    json.dumps(out, allow_nan=False)  # strictly JSON-safe
    assert out["figure"]["data"], spec.id
    assert out["chart"] == spec.id


def test_mapping_is_honoured_and_validated():
    t = Table(["a", "b", "c"], [["x", 1, 2], ["y", 3, 4]])
    spec = BY_ID["bar"]
    assert resolve(spec, t, {"x": "a", "y": ["c"]})["y"] == ["c"]
    with pytest.raises(ChartError, match="Unknown column"):
        resolve(spec, t, {"x": "nope"})


def test_missing_required_column_gives_a_helpful_message():
    with pytest.raises(ChartError, match="needs a numeric column"):
        ChartService().build(["a"], [["x"], ["y"]], "histogram")


def test_empty_result_and_unknown_chart_are_rejected():
    with pytest.raises(ChartError, match="no rows"):
        ChartService().build(["a"], [], "bar")
    with pytest.raises(ChartError, match="Unknown chart"):
        ChartService().build(["a"], [[1]], "nope")


def test_options_are_clamped_and_defaults_applied():
    spec = BY_ID["decision_tree"]
    assert parse_options(spec, {"max_depth": 99, "min_leaf": "x"}) == {
        "max_depth": 5,
        "min_leaf": 5,
    }
    assert parse_options(BY_ID["waterfall"], {"total": "false"}) == {"total": False}


def test_nan_and_infinity_never_reach_the_figure():
    rows = [
        [float("nan"), 1.0],
        [2.0, float("inf")],
        [3.0, 4.0],
        [4.0, 5.0],
        [5.0, 7.0],
    ]
    out = ChartService().build(["x", "y"], rows, "scatter")
    json.dumps(out, allow_nan=False)


def test_sankey_rejects_loops_and_roc_needs_two_classes():
    with pytest.raises(ChartError, match="loop"):
        ChartService().build(["s", "t", "v"], [["a", "b", 1], ["b", "a", 1]], "sankey")
    with pytest.raises(ChartError, match="exactly 2"):
        ChartService().build(["y", "s"], [[1, 0.2], [1, 0.4]], "roc")


def test_compatible_lists_only_drawable_charts():
    ids = ChartService().compatible(["category", "revenue"], [["a", 1.5], ["b", 2.5]])
    assert (
        "bar" in ids
        and "pie" in ids
        and "candlestick" not in ids
        and "gantt" not in ids
    )


def test_catalog_payload_is_json_and_describes_fields():
    payload = ChartService().catalog()
    json.dumps(payload)
    assert len(payload["charts"]) == 40 and payload["palette"]
    assert {"id", "label", "category", "fields", "example_sql", "options"} <= payload[
        "charts"
    ][0].keys()


def test_suggest_chart_is_unchanged():
    assert suggest_chart(["m", "v"], [["2025-01", 1], ["2025-02", 2]])["type"] == "line"
    assert suggest_chart(["n"], [[5]])["type"] == "metric"


# ---- statistics -------------------------------------------------------------
def test_roc_and_pr_on_perfect_and_tied_scores():
    _fpr, _tpr, auc = stats.roc_curve([True, True, False, False], [0.9, 0.8, 0.2, 0.1])
    assert auc == pytest.approx(1.0)
    assert stats.roc_curve([True, False], [0.5, 0.5])[2] == pytest.approx(
        0.5
    )  # ties share a threshold
    assert stats.pr_curve([True, True, False, False], [0.9, 0.8, 0.2, 0.1])[
        2
    ] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        stats.roc_curve([True, True], [0.1, 0.2])


def test_jacobi_matches_known_eigenvalues():
    assert stats.jacobi_eigenvalues([[2, 1], [1, 2]]) == pytest.approx([3.0, 1.0])
    corr = stats.correlation_matrix([[1, 2, 3, 4], [2, 4, 6, 8.5], [4, 3, 2, 1]])
    assert sum(stats.jacobi_eigenvalues(corr)) == pytest.approx(
        3.0
    )  # trace is preserved


def test_kde_integrates_to_about_one_and_pearson_edge_cases():
    xs, ys = stats.gaussian_kde([1, 2, 2, 3, 4, 7])
    area = sum(
        (ys[i] + ys[i + 1]) / 2 * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1)
    )
    assert area == pytest.approx(1.0, abs=0.02)
    assert stats.pearson([1, 1, 1], [1, 2, 3]) is None
    assert stats.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert stats.quantile([1, 2, 3, 4], 0.5) == 2.5


def test_ols_recovers_a_line():
    slope, icpt, r2 = stats.ols([0, 1, 2, 3], [1, 3, 5, 7])
    assert (slope, icpt, r2) == pytest.approx((2.0, 1.0, 1.0))


# ---- decision tree ------------------------------------------------------------
def test_tree_learns_a_separable_threshold():
    X = [[i] for i in range(40)]
    y = ["low" if i < 20 else "high" for i in range(40)]
    tree = DecisionTree("classification", 2, 3).fit(X, y)
    assert tree.root["feature"] == 0 and 19 <= tree.root["threshold"] <= 20
    assert tree.score(X, y) == 1.0 and tree.importances() == [1.0]
    assert tree.predict_one([3]) == "low" and tree.predict_one([30]) == "high"


def test_tree_regression_and_limits():
    X = [[i] for i in range(30)]
    y = [1.0 if i < 15 else 9.0 for i in range(30)]
    tree = DecisionTree("regression", 3, 3).fit(X, y)
    assert tree.score(X, y) == pytest.approx(1.0)
    assert DecisionTree("classification", 1, 1).fit(X, ["a", "b"] * 15).depth() <= 1
    with pytest.raises(ValueError):
        DecisionTree("nope")
