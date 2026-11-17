"""Microservices mode: each service alone, and the whole stack wired in-process."""
import httpx
import pytest
from fastapi.testclient import TestClient

from app.features.ask.generators import DemoGenerator
from app.features.data.client import RemoteDataClient
from app.features.history.client import RemoteHistoryClient
from services.chart_service.main import create_app as create_chart
from services.data_service.main import create_app as create_data
from services.gateway.main import create_app as create_gateway
from services.history_service.main import create_app as create_history
from services.query_service.main import create_app as create_query

TOKEN = "test-token"


def _asgi(app, name):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=f"http://{name}")


def _down():
    def handler(request):
        raise httpx.ConnectError("service is down", request=request)
    return httpx.MockTransport(handler)


@pytest.fixture()
def apps(tmp_path):
    data_app = create_data(tmp_path / "data", internal_token=TOKEN)
    history_app = create_history(tmp_path / "hist", internal_token=TOKEN)
    query_app = create_query(
        data_client=RemoteDataClient(TestClient(data_app), TOKEN),
        history_client=RemoteHistoryClient(TestClient(history_app), TOKEN),
        generator=DemoGenerator())
    return data_app, history_app, query_app


@pytest.fixture()
def gateway(apps):
    data_app, history_app, query_app = apps
    gw = create_gateway({"query": _asgi(query_app, "query"), "data": _asgi(data_app, "data"),
                         "history": _asgi(history_app, "history"), "chart": _asgi(create_chart(), "chart")})
    return TestClient(gw)


# ---- internal endpoints ------------------------------------------------------
def test_internal_endpoints_require_the_token(apps):
    data = TestClient(apps[0])
    assert data.get("/internal/schema-text").status_code == 401
    assert data.get("/internal/schema-text", headers={"X-Internal-Token": "wrong"}).status_code == 401
    ok = data.get("/internal/schema-text", headers={"X-Internal-Token": TOKEN})
    assert ok.status_code == 200 and "Table orders" in ok.json()["schema_text"]


def test_data_service_validates_before_executing(apps):
    data, h = TestClient(apps[0]), {"X-Internal-Token": TOKEN}
    assert data.post("/internal/execute", json={"sql": "DROP TABLE orders"}, headers=h).status_code == 400
    assert data.post("/internal/execute", json={"sql": "SELECT nope FROM orders"}, headers=h).status_code == 422
    good = data.post("/internal/execute", json={"sql": "SELECT COUNT(*) AS n FROM customers"}, headers=h)
    assert good.status_code == 200 and good.json()["rows"] == [[250]]


def test_history_internal_write_requires_token(apps):
    hist = TestClient(apps[1])
    body = {"question": "q", "sql": "SELECT 1", "row_count": 1, "engine": "demo"}
    assert hist.post("/internal/history", json=body).status_code == 401
    assert hist.post("/internal/history", json=body, headers={"X-Internal-Token": TOKEN}).status_code == 200
    assert hist.get("/api/history").json()["items"][0]["question"] == "q"


# ---- whole stack through the gateway -----------------------------------------
def test_gateway_ask_end_to_end_and_history(gateway):
    r = gateway.post("/api/ask", json={"question": "Orders by status"})
    assert r.status_code == 200 and r.json()["row_count"] == 4 and r.json()["chart"]["type"] == "bar"
    assert gateway.get("/api/history").json()["items"][0]["question"] == "Orders by status"
    assert "orders" in [t["name"] for t in gateway.get("/api/schema").json()["tables"]]


def test_gateway_error_codes_pass_through(gateway):
    assert gateway.post("/api/ask", json={"question": "what is the meaning of life"}).status_code == 422
    assert gateway.get("/api/nope").status_code == 404


def test_gateway_upload_and_query_schema(gateway):
    r = gateway.post("/api/upload", files={"file": ("sales.csv", b"region,units\nN,3\nS,5\n", "text/csv")})
    assert r.status_code == 200 and r.json()["table"] == "sales"
    assert "sales" in [t["name"] for t in gateway.get("/api/schema").json()["tables"]]


def test_gateway_serves_ui_and_hides_internal_routes(gateway):
    assert "QueryX" in gateway.get("/").text
    assert gateway.get("/internal/schema-text").status_code in (404, 405)
    assert gateway.get("/api/internal/schema-text").status_code == 404


def test_gateway_health_reports_all_services(gateway):
    body = gateway.get("/api/health").json()
    assert body["status"] == "ok" and set(body["services"]) == {"query", "data", "history", "chart"}


# ---- failure behavior --------------------------------------------------------
def test_gateway_returns_503_when_a_service_is_down(apps):
    _, history_app, query_app = apps
    gw = create_gateway({
        "query": _asgi(query_app, "query"),
        "data": httpx.AsyncClient(transport=_down(), base_url="http://data"),
        "history": _asgi(history_app, "history")})
    c = TestClient(gw)
    assert c.get("/api/schema").status_code == 503
    assert c.get("/api/health").json()["status"] == "degraded"


def test_answers_survive_a_history_outage(apps):
    data_app, _, _ = apps
    query_app = create_query(
        data_client=RemoteDataClient(TestClient(data_app), TOKEN),
        history_client=RemoteHistoryClient(httpx.Client(transport=_down(), base_url="http://history"), TOKEN),
        generator=DemoGenerator())
    r = TestClient(query_app).post("/api/ask", json={"question": "How many customers do we have?"})
    assert r.status_code == 200 and r.json()["rows"] == [[250]]


def test_query_service_returns_503_when_data_service_is_down():
    query_app = create_query(
        data_client=RemoteDataClient(httpx.Client(transport=_down(), base_url="http://data")),
        history_client=RemoteHistoryClient(httpx.Client(transport=_down(), base_url="http://history")),
        generator=DemoGenerator())
    assert TestClient(query_app).post("/api/ask", json={"question": "Monthly revenue"}).status_code == 503


def test_gateway_routes_charts_and_manual_sql(gateway):
    assert len(gateway.get("/api/charts").json()["charts"]) == 40
    r = gateway.post("/api/chart", json={"columns": ["c", "v"], "rows": [["a", 1], ["b", 2]], "chart": "pie"})
    assert r.status_code == 200
    sql = gateway.post("/api/sql", json={"sql": "SELECT COUNT(*) AS n FROM customers"})
    assert sql.status_code == 200 and sql.json()["rows"] == [[250]]
    assert gateway.post("/api/sql", json={"sql": "DROP TABLE orders"}).status_code == 400
