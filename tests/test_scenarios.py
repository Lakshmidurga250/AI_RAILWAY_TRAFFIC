"""Test Dynamic Scenario Creation and Baseline vs Heuristic vs AI-Optimized Comparison."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_list_standard_scenarios(client):
    res = client.get("/simulation/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 4
    types = [s["scenario_type"] for s in scenarios]
    assert "TRACK_CLOSURE" in types
    assert "SIGNAL_FAILURE" in types

def test_create_custom_scenario(client):
    res = client.post("/simulation/scenarios", json={
        "name": "Rush Hour Blizzard Slow Order",
        "scenario_type": "WEATHER",
        "description": "Subzero storm near alpine junction with 30 kmh limit",
        "parameters": {"zone": "Alpine", "speed_cap": 30.0}
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Rush Hour Blizzard Slow Order"
    assert data["scenario_type"] == "WEATHER"
    assert data["id"].startswith("SCEN_CUSTOM_")

def test_scenario_multi_tier_comparison(client):
    # Test standard track closure scenario
    res = client.post("/simulation/scenarios/SCEN_TRACK_CLOSURE_CENTRAL/compare")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "SCEN_TRACK_CLOSURE_CENTRAL"
    assert "baseline" in data
    assert "heuristic" in data
    assert "optimized" in data

    # Verify baseline > heuristic > optimized for delay
    assert data["baseline"]["total_delay_minutes"] > data["heuristic"]["total_delay_minutes"]
    assert data["heuristic"]["total_delay_minutes"] > data["optimized"]["total_delay_minutes"]

    # Verify improvement metrics
    assert data["delay_reduction_percentage"] > 0
    assert data["conflicts_avoided_percentage"] > 0
    assert data["energy_savings_percentage"] > 0
    assert "improvement_metrics" in data
    assert "throughput_gain_pct" in data["improvement_metrics"]
