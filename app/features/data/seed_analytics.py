"""Deterministic synthetic tables that make every chart type demo-able.

All values are generated (random.Random with fixed seeds) or hand-written. They are demo data,
not real measurements. Tables are created only when missing, so existing databases (including
uploaded CSV tables) are never modified or rebuilt.
"""

from __future__ import annotations

import datetime as dt
import math
import random
import sqlite3
from pathlib import Path

ANALYTICS_TABLES = (
    "daily_prices",
    "sensor_readings",
    "model_predictions",
    "learning_curve",
    "project_tasks",
    "kpi_targets",
)

DDL = {
    "daily_prices": (
        "CREATE TABLE daily_prices (trade_date TEXT PRIMARY KEY, open REAL NOT NULL, high REAL NOT NULL, "
        "low REAL NOT NULL, close REAL NOT NULL, volume INTEGER NOT NULL)"
    ),
    "sensor_readings": (
        "CREATE TABLE sensor_readings (id INTEGER PRIMARY KEY, reading_time TEXT NOT NULL, value REAL NOT NULL)"
    ),
    "model_predictions": (
        "CREATE TABLE model_predictions (id INTEGER PRIMARY KEY, actual INTEGER NOT NULL, predicted INTEGER NOT NULL, "
        "score REAL NOT NULL, baseline_score REAL NOT NULL)"
    ),
    "learning_curve": (
        "CREATE TABLE learning_curve (id INTEGER PRIMARY KEY, train_size INTEGER NOT NULL, fold INTEGER NOT NULL, "
        "train_score REAL NOT NULL, val_score REAL NOT NULL)"
    ),
    "project_tasks": (
        "CREATE TABLE project_tasks (id INTEGER PRIMARY KEY, task TEXT NOT NULL, phase TEXT NOT NULL, "
        "start_date TEXT NOT NULL, end_date TEXT NOT NULL)"
    ),
    "kpi_targets": (
        "CREATE TABLE kpi_targets (id INTEGER PRIMARY KEY, kpi TEXT NOT NULL, actual REAL NOT NULL, "
        "target REAL NOT NULL, max_value REAL NOT NULL)"
    ),
}


def _daily_prices() -> list[tuple]:
    rnd = random.Random(11)
    day, prev_close, rows = dt.date(2025, 7, 1), 100.0, []
    while len(rows) < 120:
        if day.weekday() < 5:
            open_ = prev_close * (1 + rnd.gauss(0, 0.003))
            close = open_ * (1 + rnd.gauss(0.0006, 0.013))
            high = max(open_, close) * (1 + abs(rnd.gauss(0, 0.006)))
            low = min(open_, close) * (1 - abs(rnd.gauss(0, 0.006)))
            rows.append(
                (
                    day.isoformat(),
                    round(open_, 2),
                    round(high, 2),
                    round(low, 2),
                    round(close, 2),
                    rnd.randint(800_000, 2_000_000),
                )
            )
            prev_close = close
        day += dt.timedelta(days=1)
    return rows


def _sensor_readings() -> list[tuple]:
    rnd = random.Random(5)
    start = dt.datetime(2025, 12, 1, 0, 0, tzinfo=dt.timezone.utc)
    rows = []
    for i in range(80):
        value = rnd.gauss(50, 1.2) + (
            0.9 if 45 <= i < 60 else 0.0
        )  # small mean shift mid-run
        if i == 23:
            value = 56.4  # out-of-control spike
        if i == 61:
            value = 43.7  # out-of-control dip
        rows.append(
            (
                i + 1,
                (start + dt.timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S"),
                round(value, 2),
            )
        )
    return rows


def _model_predictions() -> list[tuple]:
    rnd = random.Random(7)

    def clip(v: float) -> float:
        return min(0.99, max(0.01, v))

    rows = []
    for i in range(1, 401):
        actual = 1 if rnd.random() < 0.35 else 0
        score = clip(rnd.gauss(0.68 if actual else 0.34, 0.18))
        baseline = clip(rnd.gauss(0.56 if actual else 0.46, 0.22))
        rows.append(
            (i, actual, 1 if score >= 0.5 else 0, round(score, 4), round(baseline, 4))
        )
    return rows


def _learning_curve() -> list[tuple]:
    rnd = random.Random(3)
    rows, rid = [], 1
    for size in (50, 100, 200, 300, 400, 500, 600, 700, 800, 1000):
        for fold in range(1, 6):
            train = 1.0 - 0.13 * (1 - math.exp(-size / 300)) + rnd.gauss(0, 0.005)
            val = 0.60 + 0.24 * (1 - math.exp(-size / 260)) + rnd.gauss(0, 0.018)
            rows.append((rid, size, fold, round(train, 4), round(val, 4)))
            rid += 1
    return rows


PROJECT_TASKS = [
    ("Requirements gathering", "Planning", "2026-01-05", "2026-01-16"),
    ("System design", "Planning", "2026-01-12", "2026-01-30"),
    ("Data collection", "Data", "2026-01-19", "2026-02-13"),
    ("Data cleaning", "Data", "2026-02-09", "2026-02-27"),
    ("Feature engineering", "Modeling", "2026-02-23", "2026-03-13"),
    ("Model training", "Modeling", "2026-03-09", "2026-04-03"),
    ("Evaluation", "Modeling", "2026-03-30", "2026-04-17"),
    ("Web app development", "Delivery", "2026-03-02", "2026-04-24"),
    ("Testing and QA", "Delivery", "2026-04-13", "2026-05-08"),
    ("Deployment", "Delivery", "2026-05-04", "2026-05-15"),
]

KPI_TARGETS = [
    ("Revenue (k$)", 270, 300, 400),
    ("New customers", 182, 150, 250),
    ("Satisfaction (%)", 88, 90, 100),
    ("On-time delivery (%)", 94, 95, 100),
    ("Tickets resolved", 410, 380, 500),
]


def _rows(table: str) -> tuple[str, list[tuple]]:
    if table == "daily_prices":
        return "INSERT INTO daily_prices VALUES (?,?,?,?,?,?)", _daily_prices()
    if table == "sensor_readings":
        return "INSERT INTO sensor_readings VALUES (?,?,?)", _sensor_readings()
    if table == "model_predictions":
        return "INSERT INTO model_predictions VALUES (?,?,?,?,?)", _model_predictions()
    if table == "learning_curve":
        return "INSERT INTO learning_curve VALUES (?,?,?,?,?)", _learning_curve()
    if table == "project_tasks":
        return "INSERT INTO project_tasks VALUES (?,?,?,?,?)", [
            (i + 1, *t) for i, t in enumerate(PROJECT_TASKS)
        ]
    return "INSERT INTO kpi_targets VALUES (?,?,?,?,?)", [
        (i + 1, *t) for i, t in enumerate(KPI_TARGETS)
    ]


def add_missing(path: Path | str) -> list[str]:
    """Create and fill any analytics demo table that does not exist yet. Returns the names added."""
    conn = sqlite3.connect(path)
    added: list[str] = []
    try:
        existing = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        with conn:
            for table in ANALYTICS_TABLES:
                if table in existing:
                    continue
                sql, rows = _rows(table)
                conn.execute(DDL[table])
                conn.executemany(sql, rows)
                added.append(table)
    finally:
        conn.close()
    return added
