"""Test Observability, Health Probes, Prometheus Metrics, and Security Headers."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health_general(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "simulation_running" in data
    assert "active_trains" in data

def test_liveness_probe(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ALIVE"

def test_readiness_probe(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["READY", "DEGRADED"]
    assert "database" in data
    assert "simulation_engine" in data

def test_security_headers_middleware(client):
    res = client.get("/health")
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-transport-security" in res.headers

def test_prometheus_metrics_endpoint(client):
    # Perform a couple requests to populate metrics
    client.get("/api/stations")
    client.get("/health")

    res = client.get("/metrics")
    assert res.status_code == 200
    text = res.text
    assert "railway_http_requests_total" in text
    assert "railway_active_trains" in text
