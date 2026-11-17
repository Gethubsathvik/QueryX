import pytest
from fastapi.testclient import TestClient

from app.features.ask.generators import DemoGenerator, GeneratedSQL
from app.main import create_app


class EvilGenerator:
    name = "evil"

    def generate(self, question, schema_text):
        return GeneratedSQL("DROP TABLE orders", "oops")

    def repair(self, *a):
        raise AssertionError("unsafe SQL must not be repaired")


class FlakyGenerator:
    """First query references a bad column; the repair fixes it."""
    name = "flaky"

    def generate(self, question, schema_text):
        return GeneratedSQL("SELECT nope FROM customers", "bad")

    def repair(self, question, schema_text, bad_sql, error):
        return GeneratedSQL("SELECT COUNT(*) AS customers FROM customers", "fixed")


@pytest.fixture()
def client(tmp_path):
    return TestClient(create_app(tmp_path, generator=DemoGenerator()))


def test_health_and_schema(client):
    assert client.get("/api/health").json() == {"status": "ok", "engine": "demo", "mode": "monolith"}
    names = [t["name"] for t in client.get("/api/schema").json()["tables"]]
    assert "orders" in names


def test_index_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "QueryX" in r.text


def test_ask_returns_sql_rows_and_chart(client):
    r = client.post("/api/ask", json={"question": "Monthly revenue"})
    assert r.status_code == 200
    body = r.json()
    assert body["sql"].lower().startswith("select") and body["row_count"] > 12
    assert body["chart"]["type"] == "line" and body["chart"]["x"] == "month"


def test_ask_top_n(client):
    body = client.post("/api/ask", json={"question": "top 3 customers by revenue"}).json()
    assert body["row_count"] == 3 and body["chart"]["type"] == "bar"


def test_unsupported_question_is_422(client):
    r = client.post("/api/ask", json={"question": "what is the meaning of life"})
    assert r.status_code == 422 and "Demo mode" in r.json()["detail"]


def test_short_question_rejected(client):
    assert client.post("/api/ask", json={"question": "  a "}).status_code == 422


def test_unsafe_sql_is_blocked_and_data_survives(tmp_path):
    c = TestClient(create_app(tmp_path, generator=EvilGenerator()))
    r = c.post("/api/ask", json={"question": "delete everything please"})
    assert r.status_code == 400 and "Blocked unsafe SQL" in r.json()["detail"]
    tables = [t["name"] for t in c.get("/api/schema").json()["tables"]]
    assert "orders" in tables


def test_failed_sql_is_repaired_once(tmp_path):
    c = TestClient(create_app(tmp_path, generator=FlakyGenerator()))
    body = c.post("/api/ask", json={"question": "how many customers"}).json()
    assert body["attempts"] == 2 and body["rows"] == [[250]]


def test_upload_then_schema_and_history(client):
    r = client.post("/api/upload", files={"file": ("sales.csv", b"region,units\nN,3\nS,5\n", "text/csv")})
    assert r.status_code == 200 and r.json()["table"] == "sales"
    assert "sales" in [t["name"] for t in client.get("/api/schema").json()["tables"]]
    assert client.post("/api/upload", files={"file": ("x.txt", b"hi", "text/plain")}).status_code == 400

    client.post("/api/ask", json={"question": "Orders by status"})
    items = client.get("/api/history").json()["items"]
    assert items and items[0]["question"] == "Orders by status"


# ---- editable SQL bar and chart studio --------------------------------------------
def test_manual_sql_runs_through_the_same_safety_pipeline(client):
    r = client.post("/api/sql", json={"sql": "SELECT COUNT(*) AS n FROM customers"})
    assert r.status_code == 200
    body = r.json()
    assert body["engine"] == "manual" and body["rows"] == [[250]] and body["chart"]["type"] == "metric"
    assert client.post("/api/sql", json={"sql": "DROP TABLE orders"}).status_code == 400
    assert client.post("/api/sql", json={"sql": "SELECT * FROM sqlite_master"}).status_code in (400, 422)
    assert client.post("/api/sql", json={"sql": "SELECT nope FROM orders"}).status_code == 422
    assert client.post("/api/sql", json={"sql": "   "}).status_code in (422,)
    assert client.post("/api/sql", json={"sql": ""}).status_code == 422


def test_manual_sql_is_logged_in_history(client):
    client.post("/api/sql", json={"sql": "SELECT 1 AS one"})
    items = client.get("/api/history").json()["items"]
    assert items and items[0]["engine"] == "manual"


def test_chart_endpoints(client):
    cat = client.get("/api/charts").json()
    assert len(cat["charts"]) == 40
    r = client.post("/api/chart", json={"columns": ["c", "v"], "rows": [["a", 1], ["b", 2]], "chart": "bar"})
    assert r.status_code == 200 and r.json()["figure"]["data"][0]["type"] == "bar"
    bad = client.post("/api/chart", json={"columns": ["c"], "rows": [["a"]], "chart": "histogram"})
    assert bad.status_code == 422 and "numeric" in bad.json()["detail"]
    ok = client.post("/api/charts/compatible", json={"columns": ["c", "v"], "rows": [["a", 1], ["b", 2]]})
    assert "bar" in ok.json()["compatible"]
