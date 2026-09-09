"""FastAPI API Integration Tests."""
import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_get_dashboard_html(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AI RAILWAY TRAFFIC CONTROL" in response.text

def test_get_trains(client: TestClient):
    response = client.get("/trains")
    assert response.status_code == 200
    trains = response.json()
    assert isinstance(trains, list)
    assert len(trains) >= 4

def test_get_stations(client: TestClient):
    response = client.get("/stations")
    assert response.status_code == 200
    stations = response.json()
    assert len(stations) >= 10

def test_get_network_graph(client: TestClient):
    response = client.get("/network/graph")
    assert response.status_code == 200
    graph = response.json()
    assert "nodes" in graph
    assert "edges" in graph

def test_simulation_status(client: TestClient):
    response = client.get("/simulation/status")
    assert response.status_code == 200
    status = response.json()
    assert "time_acceleration" in status

def test_ai_delay_prediction(client: TestClient):
    response = client.post("/ai/delay", json={"train_id": "TR_101", "horizon_minutes": 15})
    assert response.status_code == 200
    pred = response.json()
    assert "predicted_delay_minutes" in pred
    assert "confidence" in pred

def test_ai_congestion_prediction(client: TestClient):
    response = client.post("/ai/congestion", json={"resource_type": "STATION", "resource_id": "ST_CENTRAL", "horizon_minutes": 15})
    assert response.status_code == 200
    data = response.json()
    assert "congestion_score" in data

def test_optimization_route(client: TestClient):
    response = client.post("/optimization/route", json={
        "train_id": "TR_TEST",
        "origin_station_id": "ST_SOUTH",
        "destination_station_id": "ST_NORTH",
        "algorithm": "A_STAR"
    })
    assert response.status_code == 200
    data = response.json()
    assert "optimal_route" in data

def test_analytics_dashboard(client: TestClient):
    response = client.get("/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "punctuality_rate" in data["kpis"]

def test_reports_operational(client: TestClient):
    response = client.get("/reports/operational?format=json")
    assert response.status_code == 200
    data = response.json()
    assert "executive_summary" in data
