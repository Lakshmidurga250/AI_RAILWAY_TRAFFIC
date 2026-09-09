"""Test AI Model Registry Lifecycle, Versioning, Evaluation, and Retraining."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_list_and_get_models(client):
    res = client.get("/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 4
    delay_mod = next(m for m in models if m["id"] == "MOD_DELAY_GBM_V1")
    assert delay_mod["task"] == "DELAY_PREDICTION"
    assert "metrics" in delay_mod

    # Single model query
    res_single = client.get("/models/MOD_DELAY_GBM_V1")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == "MOD_DELAY_GBM_V1"

def test_evaluate_model(client):
    res = client.post("/models/MOD_DELAY_GBM_V1/evaluate")
    assert res.status_code == 200
    data = res.json()
    assert data["model_id"] == "MOD_DELAY_GBM_V1"
    assert data["validation_status"] == "PASSED_BENCHMARK"
    assert "current_metrics" in data
    assert "baseline_metrics" in data

def test_train_model_and_versions(client):
    res_initial = client.get("/models/MOD_DELAY_GBM_V1")
    initial_version = res_initial.json()["version"]

    # Trigger training
    res_train = client.post("/models/MOD_DELAY_GBM_V1/train", json={
        "hyperparameters": {"n_estimators": 120, "learning_rate": 0.05},
        "dataset": "augmented_corridor_telemetry_2026_q2"
    })
    assert res_train.status_code == 200
    retrained = res_train.json()
    assert retrained["version"] != initial_version
    assert retrained["status"] == "VALIDATED"

    # Verify version history
    res_history = client.get("/models/MOD_DELAY_GBM_V1/versions")
    assert res_history.status_code == 200
    history = res_history.json()
    assert history["model_id"] == "MOD_DELAY_GBM_V1"
    assert len(history["versions"]) >= 3

    # Promote to ACTIVE
    res_status = client.put("/models/MOD_DELAY_GBM_V1/status?status=ACTIVE")
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "SUCCESS"

    # Confirm updated status
    res_active = client.get("/models/MOD_DELAY_GBM_V1")
    assert res_active.json()["status"] == "ACTIVE"
