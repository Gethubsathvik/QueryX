"""The catalog of chart types: what data each needs, its options, and an example query.

The catalog is data, not code: the API serves it to the UI, which builds the column pickers
and the gallery from it. Builders live in `builders/` and are registered by chart id.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .errors import ChartError


@dataclass(frozen=True)
class Field:
    role: str
    label: str
    kinds: tuple[str, ...]          # what the column may be, in priority order: number|date|text|category
    required: bool = True
    multiple: bool = False
    auto: bool | str = True         # True = auto-fill, False = never, "hint" = only if a column name matches
    hints: tuple[str, ...] = ()     # column-name fragments that identify this role (e.g. "open" for candlesticks)
    prefer: str = ""                # "low" / "high" cardinality or "last" column when several qualify
    max_auto: int = 1               # how many columns a multiple field auto-fills
    min_count: int = 1              # minimum columns for a multiple field


@dataclass(frozen=True)
class Option:
    name: str
    label: str
    type: str                       # select | number | bool
    default: object
    choices: tuple = ()
    min: float | None = None
    max: float | None = None


@dataclass(frozen=True)
class ChartSpec:
    id: str
    label: str
    category: str
    description: str
    fields: tuple[Field, ...]
    example_sql: str
    options: tuple[Option, ...] = ()


CATEGORIES = [
    ("compare", "Compare and trend"),
    ("distribution", "Distribution"),
    ("relationship", "Relationship"),
    ("composition", "Part-to-whole and flow"),
    ("performance", "Performance and process"),
    ("finance", "Finance"),
    ("ml", "Machine learning"),
]

# ---------------------------------------------------------------------------- example SQL
_REV = "ROUND(SUM(oi.quantity * oi.unit_price), 2)"
_ITEMS = "FROM orders o JOIN order_items oi ON oi.order_id = o.id"
_DONE = "WHERE o.status = 'completed'"
_CUSTOMER = ("FROM customers c JOIN orders o ON o.customer_id = c.id "
             "JOIN order_items oi ON oi.order_id = o.id WHERE o.status = 'completed' GROUP BY c.id")
_CAT = "JOIN products p ON p.id = oi.product_id"
_CUST = "JOIN customers c ON c.id = o.customer_id"
_AOV = "ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.id), 2)"

SQL_CATEGORY_REVENUE = (f"SELECT p.category AS category, {_REV} AS revenue {_ITEMS} {_CAT} {_DONE} "
                        "GROUP BY p.category ORDER BY revenue DESC")
SQL_MONTHLY = (f"SELECT strftime('%Y-%m', o.order_date) AS month, {_REV} AS revenue {_ITEMS} {_DONE} "
               "GROUP BY month ORDER BY month")
SQL_MONTHLY_CATEGORY = (f"SELECT strftime('%Y-%m', o.order_date) AS month, p.category AS category, {_REV} AS revenue "
                        f"{_ITEMS} {_CAT} {_DONE} GROUP BY month, p.category ORDER BY month")
SQL_COUNTRY_CATEGORY = (f"SELECT c.country AS country, p.category AS category, {_REV} AS revenue "
                        f"{_ITEMS} {_CUST} {_CAT} {_DONE} GROUP BY c.country, p.category")
SQL_CUSTOMER_REVENUE = f"SELECT c.segment AS segment, {_REV} AS total_revenue {_CUSTOMER}"
SQL_CUSTOMER_AOV = f"SELECT c.segment AS segment, {_AOV} AS avg_order_value {_CUSTOMER}"
SQL_CUSTOMER_FEATURES = (
    "SELECT c.segment AS segment, COUNT(DISTINCT o.id) AS orders, SUM(oi.quantity) AS items, "
    f"{_REV} AS revenue, {_AOV} AS avg_order_value, ROUND(AVG(oi.unit_price), 2) AS avg_price, "
    "CAST(julianday('2025-12-31') - julianday(c.signup_date) AS INTEGER) AS tenure_days " + _CUSTOMER)
SQL_CUSTOMER_NUMERIC = SQL_CUSTOMER_FEATURES.replace("SELECT c.segment AS segment, ", "SELECT ", 1)
SQL_DAILY = "SELECT trade_date, open, high, low, close FROM daily_prices ORDER BY trade_date"


def _f(role, label, kinds, **kw) -> Field:
    return Field(role, label, tuple(kinds), **kw)


AGG = Option("agg", "Aggregate repeated values", "select", "sum", ("sum", "mean", "count", "min", "max"))

# Reusable fields
X_CAT = _f("x", "Category (X)", ("category", "date"))
Y_NUM_MULTI = _f("y", "Value (Y)", ("number",), multiple=True, max_auto=3)
GROUP_OPT = _f("group", "Group / series", ("text",), required=False, auto=True, prefer="low")
GROUP_OFF = _f("group", "Group / series", ("text",), required=False, auto=False)
X_LINE = _f("x", "X axis", ("date", "category", "number"))

CATALOG: tuple[ChartSpec, ...] = (
    # ---- compare and trend -------------------------------------------------------------
    ChartSpec("bar", "Bar chart", "compare", "Compare a value across categories.",
              (X_CAT, GROUP_OFF, Y_NUM_MULTI), SQL_CATEGORY_REVENUE, (AGG,)),
    ChartSpec("hbar", "Horizontal bar chart", "compare", "Ranked categories with long labels.",
              (X_CAT, GROUP_OFF, Y_NUM_MULTI),
              f"SELECT p.name AS product, {_REV} AS revenue {_ITEMS} {_CAT} {_DONE} "
              "GROUP BY p.id ORDER BY revenue DESC LIMIT 10", (AGG,)),
    ChartSpec("grouped_bar", "Grouped bar chart", "compare", "Side-by-side bars for each group within a category.",
              (X_CAT, GROUP_OPT, Y_NUM_MULTI),
              f"SELECT p.category AS category, c.segment AS segment, {_REV} AS revenue {_ITEMS} {_CUST} {_CAT} {_DONE} "
              "GROUP BY p.category, c.segment ORDER BY p.category", (AGG,)),
    ChartSpec("stacked_bar", "Stacked bar chart", "compare", "Stack groups to show totals and their composition.",
              (X_CAT, GROUP_OPT, Y_NUM_MULTI),
              f"SELECT c.country AS country, c.segment AS segment, {_REV} AS revenue {_ITEMS} {_CUST} {_DONE} "
              "GROUP BY c.country, c.segment", (AGG,)),
    ChartSpec("line", "Line chart", "compare", "Show how values change along an ordered axis.",
              (X_LINE, GROUP_OPT, Y_NUM_MULTI), SQL_MONTHLY),
    ChartSpec("area", "Area chart", "compare", "A line chart with the area filled; stack to show composition over time.",
              (X_LINE, GROUP_OPT, Y_NUM_MULTI), SQL_MONTHLY_CATEGORY,
              (Option("stacked", "Stack series", "bool", True),)),
    ChartSpec("time_series", "Time-series chart", "compare", "Date-based line with a range slider and quick range buttons.",
              (_f("x", "Date / time (X)", ("date",)), GROUP_OPT, Y_NUM_MULTI),
              "SELECT trade_date, close FROM daily_prices ORDER BY trade_date"),
    ChartSpec("pie", "Pie chart", "composition", "Share of each category in a total (best with 6 or fewer slices).",
              (_f("label", "Slice label", ("category", "date")), _f("value", "Slice size", ("number",))),
              f"SELECT c.country AS country, {_REV} AS revenue {_ITEMS} {_CUST} {_DONE} "
              "GROUP BY c.country ORDER BY revenue DESC", (AGG,)),
    ChartSpec("doughnut", "Doughnut chart", "composition", "A pie chart with a hole, easier to read and label.",
              (_f("label", "Slice label", ("category", "date")), _f("value", "Slice size", ("number",))),
              "SELECT status, COUNT(*) AS orders FROM orders GROUP BY status ORDER BY orders DESC", (AGG,)),
    # ---- distribution ------------------------------------------------------------------
    ChartSpec("histogram", "Histogram", "distribution", "How many values fall into each range (bin).",
              (_f("x", "Values", ("number",)), GROUP_OFF), SQL_CUSTOMER_REVENUE,
              (Option("bins", "Number of bins (0 = auto)", "number", 0, min=0, max=100),
               Option("norm", "Y axis", "select", "", ("", "percent", "probability density")))),
    ChartSpec("box", "Box plot", "distribution", "Median, quartiles, whiskers and outliers per group.",
              (_f("group", "Group (X)", ("text",), required=False, prefer="low"),
               _f("y", "Values (Y)", ("number",), multiple=True, max_auto=4)), SQL_CUSTOMER_REVENUE),
    ChartSpec("violin", "Violin plot", "distribution", "Distribution shape per group, with an inner box plot.",
              (_f("group", "Group (X)", ("text",), required=False, prefer="low"),
               _f("y", "Values (Y)", ("number",), multiple=True, max_auto=4)),
              f"SELECT c.country AS country, {_REV} AS total_revenue {_CUSTOMER}"),
    ChartSpec("density", "Density plot", "distribution", "A smooth estimate (KDE) of the distribution.",
              (_f("x", "Values", ("number",)), GROUP_OPT), SQL_CUSTOMER_AOV),
    ChartSpec("qq", "Q-Q plot", "distribution", "Compares your data with a normal distribution; a straight line means normal.",
              (_f("y", "Values", ("number",)),), SQL_CUSTOMER_REVENUE),
    ChartSpec("error_bar", "Error bar chart", "distribution", "Mean per category with a 95% confidence interval (or your own error column).",
              (_f("x", "Category (X)", ("text", "date", "category")), _f("y", "Value (Y)", ("number",)),
               _f("error", "Error column (optional)", ("number",), required=False, auto="hint",
                  hints=("err", "ci", "sd", "std"))), SQL_CUSTOMER_REVENUE),
    ChartSpec("rug", "Rug plot", "distribution", "Every observation as a tick mark, with a histogram above.",
              (_f("x", "Values", ("number",)),), SQL_CUSTOMER_AOV),
    # ---- relationship ------------------------------------------------------------------
    ChartSpec("scatter", "Scatter plot", "relationship", "Relationship between two numbers, with an optional trend line.",
              (_f("x", "X", ("number",)), _f("y", "Y", ("number",)), GROUP_OPT,
               _f("label", "Hover label", ("text",), required=False, auto=False)),
              "SELECT c.segment AS segment, COUNT(DISTINCT o.id) AS orders, "
              f"{_REV} AS revenue {_CUSTOMER}",
              (Option("trendline", "Trend line", "bool", True),)),
    ChartSpec("bubble", "Bubble chart", "relationship", "A scatter plot where a third number sets the bubble size.",
              (_f("x", "X", ("number",)), _f("y", "Y", ("number",)), _f("size", "Bubble size", ("number",)),
               GROUP_OPT, _f("label", "Hover label", ("text",), required=False, prefer="high")),
              "SELECT p.name AS product, p.category AS category, p.price AS price, SUM(oi.quantity) AS units_sold, "
              f"{_REV} AS revenue FROM products p JOIN order_items oi ON oi.product_id = p.id "
              "JOIN orders o ON o.id = oi.order_id WHERE o.status = 'completed' GROUP BY p.id"),
    ChartSpec("heatmap", "Heatmap", "relationship", "Colour-coded grid of a value for two categories.",
              (_f("x", "Columns (X)", ("category", "date")), _f("y", "Rows (Y)", ("category", "date")),
               _f("value", "Value", ("number",))), SQL_COUNTRY_CATEGORY, (AGG,)),
    ChartSpec("correlation_matrix", "Correlation matrix", "relationship", "Pearson correlation between every pair of numeric columns.",
              (_f("columns", "Numeric columns", ("number",), multiple=True, max_auto=12, min_count=2),),
              SQL_CUSTOMER_NUMERIC),
    ChartSpec("scatter3d", "3D scatter plot", "relationship", "Three numbers as points in 3D; drag to rotate.",
              (_f("x", "X", ("number",)), _f("y", "Y", ("number",)), _f("z", "Z", ("number",)), GROUP_OPT),
              "SELECT c.segment AS segment, COUNT(DISTINCT o.id) AS orders, ROUND(AVG(oi.unit_price), 2) AS avg_price, "
              f"{_REV} AS revenue {_CUSTOMER}"),
    ChartSpec("surface3d", "3D surface plot", "relationship", "A value over a grid of two categories or numbers, as a surface.",
              (_f("x", "X axis", ("date", "text", "category", "number")),
               _f("y", "Y axis", ("text", "date", "category", "number")), _f("z", "Height (Z)", ("number",))),
              SQL_MONTHLY_CATEGORY, (AGG,)),
    # ---- part-to-whole and flow --------------------------------------------------------
    ChartSpec("treemap", "Treemap", "composition", "Nested rectangles sized by value; one text column per level.",
              (_f("path", "Hierarchy (outer to inner)", ("text",), multiple=True, max_auto=3),
               _f("value", "Size", ("number",))),
              f"SELECT p.category AS category, p.name AS product, {_REV} AS revenue {_ITEMS} {_CAT} {_DONE} GROUP BY p.id"),
    ChartSpec("sunburst", "Sunburst chart", "composition", "A radial treemap: rings are hierarchy levels.",
              (_f("path", "Hierarchy (inner to outer)", ("text",), multiple=True, max_auto=3),
               _f("value", "Size", ("number",))),
              "SELECT country, segment, COUNT(*) AS customers FROM customers GROUP BY country, segment"),
    ChartSpec("marimekko", "Marimekko chart", "composition", "Column width = category total, segment height = share within it.",
              (_f("x", "Columns (X)", ("text", "date", "category")), _f("group", "Segments", ("text",)),
               _f("value", "Value", ("number",))), SQL_COUNTRY_CATEGORY),
    ChartSpec("funnel", "Funnel chart", "composition", "Drop-off through ordered stages.",
              (_f("stage", "Stage", ("text", "category")), _f("value", "Count", ("number",))),
              "SELECT '1. Orders placed' AS stage, COUNT(*) AS orders FROM orders "
              "UNION ALL SELECT '2. Not cancelled', COUNT(*) FROM orders WHERE status <> 'cancelled' "
              "UNION ALL SELECT '3. Processed (paid)', COUNT(*) FROM orders WHERE status IN ('completed', 'refunded') "
              "UNION ALL SELECT '4. Completed, not refunded', COUNT(*) FROM orders WHERE status = 'completed'"),
    ChartSpec("waterfall", "Waterfall chart", "composition", "How increments add up to a total.",
              (_f("x", "Step label", ("text", "date", "category")), _f("y", "Change", ("number",))),
              SQL_CATEGORY_REVENUE, (Option("total", "Add a total bar", "bool", True),)),
    ChartSpec("sankey", "Sankey diagram", "composition", "Flows between nodes; link width is the amount.",
              (_f("source", "Source", ("text",)), _f("target", "Target", ("text",)), _f("value", "Flow size", ("number",))),
              f"SELECT c.segment AS source, p.category AS target, {_REV} AS value {_ITEMS} {_CUST} {_CAT} {_DONE} "
              "GROUP BY c.segment, p.category"),
    # ---- performance and process -------------------------------------------------------
    ChartSpec("gantt", "Gantt chart", "performance", "Tasks as bars from start date to end date.",
              (_f("task", "Task", ("text",)),
               _f("start", "Start date", ("date",), hints=("start", "begin")),
               _f("end", "End date", ("date",), hints=("end", "finish", "due")),
               _f("group", "Colour by", ("text",), required=False, prefer="low")),
              "SELECT task, phase, start_date, end_date FROM project_tasks ORDER BY start_date"),
    ChartSpec("bullet", "Bullet chart", "performance", "Actual versus target on a banded scale.",
              (_f("label", "Measure", ("text", "category")),
               _f("value", "Actual", ("number",), hints=("actual", "value", "current")),
               _f("target", "Target", ("number",), required=False, hints=("target", "goal", "plan", "budget")),
               _f("max", "Scale maximum (optional)", ("number",), required=False, auto="hint",
                  hints=("max", "limit", "cap", "range"))),
              "SELECT kpi, actual, target, max_value FROM kpi_targets"),
    ChartSpec("radar", "Radar chart", "performance", "Compare items across several metrics on one polar plot.",
              (_f("label", "Item (one shape each)", ("text", "category")),
               _f("metrics", "Metrics (axes)", ("number",), multiple=True, max_auto=8, min_count=3)),
              "SELECT c.country AS country, COUNT(DISTINCT c.id) AS customers, COUNT(DISTINCT o.id) AS orders, "
              "ROUND(SUM(oi.quantity * oi.unit_price) / 1000.0, 1) AS revenue_k, ROUND(AVG(oi.unit_price), 1) AS avg_price, "
              "ROUND(AVG(oi.quantity), 2) AS avg_quantity FROM customers c JOIN orders o ON o.customer_id = c.id "
              "JOIN order_items oi ON oi.order_id = o.id WHERE o.status = 'completed' GROUP BY c.country",
              (Option("normalize", "Scale each metric to 0-100", "bool", True),)),
    ChartSpec("control_chart", "Control chart", "performance", "Process measurements with centre line and control limits (I-MR).",
              (_f("x", "Sequence / time (X)", ("date", "category", "number")), _f("y", "Measurement", ("number",))),
              "SELECT reading_time, value FROM sensor_readings ORDER BY reading_time",
              (Option("sigma", "Control limit (sigma)", "number", 3, min=1, max=6),)),
    # ---- finance -----------------------------------------------------------------------
    ChartSpec("candlestick", "Candlestick chart", "finance", "Open, high, low and close per period as candles.",
              (_f("x", "Date", ("date",)),
               _f("open", "Open", ("number",), hints=("open",)), _f("high", "High", ("number",), hints=("high",)),
               _f("low", "Low", ("number",), hints=("low",)), _f("close", "Close", ("number",), hints=("close",))),
              SQL_DAILY),
    ChartSpec("ohlc", "OHLC chart", "finance", "Open-high-low-close bars: the classic stock chart.",
              (_f("x", "Date", ("date",)),
               _f("open", "Open", ("number",), hints=("open",)), _f("high", "High", ("number",), hints=("high",)),
               _f("low", "Low", ("number",), hints=("low",)), _f("close", "Close", ("number",), hints=("close",))),
              SQL_DAILY),
    # ---- machine learning --------------------------------------------------------------
    ChartSpec("scree", "Scree plot", "ml", "PCA: variance explained by each principal component.",
              (_f("columns", "Numeric columns", ("number",), multiple=True, max_auto=12, min_count=2),),
              SQL_CUSTOMER_NUMERIC),
    ChartSpec("roc", "ROC curve", "ml", "True-positive vs false-positive rate across thresholds, with AUC.",
              (_f("actual", "Actual label (2 classes)", ("category", "number"), hints=("actual", "label", "truth", "target")),
               _f("score", "Predicted score(s)", ("number",), multiple=True, max_auto=4,
                  hints=("score", "prob", "confidence"))),
              "SELECT actual, score, baseline_score FROM model_predictions",
              (Option("positive", "Positive class (blank = auto)", "text", ""),)),
    ChartSpec("pr", "Precision-recall curve", "ml", "Precision vs recall across thresholds, with average precision.",
              (_f("actual", "Actual label (2 classes)", ("category", "number"), hints=("actual", "label", "truth", "target")),
               _f("score", "Predicted score(s)", ("number",), multiple=True, max_auto=4,
                  hints=("score", "prob", "confidence"))),
              "SELECT actual, score, baseline_score FROM model_predictions",
              (Option("positive", "Positive class (blank = auto)", "text", ""),)),
    ChartSpec("confusion_matrix", "Confusion matrix", "ml", "Counts of actual vs predicted classes.",
              (_f("actual", "Actual", ("category",), hints=("actual", "truth", "label")),
               _f("predicted", "Predicted", ("category",), hints=("pred",)),
               _f("count", "Count (optional)", ("number",), required=False, auto="hint", hints=("count", "freq", "total"))),
              "SELECT actual, predicted FROM model_predictions",
              (Option("normalize", "Show", "select", "counts", ("counts", "row percent")),)),
    ChartSpec("learning_curve", "Learning curve", "ml", "Training and validation score as the training set grows.",
              (_f("x", "Training size (X)", ("number",), hints=("size", "samples")),
               _f("y", "Score column(s)", ("number",), multiple=True, max_auto=4,
                  hints=("score", "train", "val", "test"))),
              "SELECT train_size, train_score, val_score FROM learning_curve ORDER BY train_size"),
    ChartSpec("decision_tree", "Decision tree", "ml", "A small CART tree that predicts a target column from numeric features.",
              (_f("target", "Target to predict", ("text", "category", "number"), prefer="last"),
               _f("features", "Numeric features", ("number",), multiple=True, max_auto=10)),
              "SELECT SUM(oi.quantity) AS items, ROUND(AVG(oi.unit_price), 2) AS avg_price, "
              "CAST(julianday('2025-12-31') - julianday(c.signup_date) AS INTEGER) AS tenure_days, "
              "CASE WHEN SUM(oi.quantity * oi.unit_price) > 2800 THEN 'high_value' ELSE 'standard' END AS customer_type "
              + _CUSTOMER,
              (Option("max_depth", "Maximum depth", "number", 3, min=1, max=5),
               Option("min_leaf", "Minimum samples per leaf", "number", 5, min=1, max=100))),
)

BY_ID: dict[str, ChartSpec] = {c.id: c for c in CATALOG}


def get_spec(chart_id: str) -> ChartSpec:
    try:
        return BY_ID[chart_id]
    except KeyError:
        raise ChartError(f"Unknown chart type '{chart_id}'.") from None


def catalog_payload() -> dict:
    return {
        "categories": [{"id": i, "label": label} for i, label in CATEGORIES],
        "charts": [asdict(c) for c in CATALOG],
    }
