"""Tests for Historical Replay and What-If Simulation Engines."""
import pytest
from datetime import datetime, timezone
from simulation.engine.replay import HistoricalReplayEngine
from simulation.engine.what_if import WhatIfSimulationEngine

def test_historical_replayer_record_and_scrub():
    replayer = HistoricalReplayEngine()
    replayer.clear()
    
    now = datetime.now(timezone.utc)
    for i in range(10):
        replayer.record_step(now, i, {"step": i, "trains": [{"id": "TR_1", "speed_kmh": 50 + i}]})

    summary = replayer.get_timeline_summary()
    assert summary["total_snapshots"] == 10
    assert summary["cursor_index"] == 0

    frame_5 = replayer.seek_to_index(5)
    assert frame_5 is not None
    assert frame_5["step"] == 5

    # Test forward and backward stepping
    fwd = replayer.step_forward()
    assert fwd["step"] == 6

    bwd = replayer.step_backward()
    assert bwd["step"] == 5

def test_what_if_delay_injection_scenario():
    res = WhatIfSimulationEngine.evaluate_what_if_scenario(
        intervention_type="INJECT_TRAIN_DELAY",
        parameters={"train_id": "TR_101", "delay_minutes": 20.0},
        horizon_minutes=15
    )
    assert res["scenario_type"] == "WHAT_IF_COUNTERFACTUAL"
    assert "baseline_metrics" in res
    assert "what_if_metrics" in res
    assert "differential_impact" in res
    assert "severity_assessment" in res["differential_impact"]

def test_what_if_track_closure_scenario():
    res = WhatIfSimulationEngine.evaluate_what_if_scenario(
        intervention_type="TRACK_CLOSURE",
        parameters={"track_id": "TRK_GUT_MBL_UP"},
        horizon_minutes=15
    )
    assert res["scenario_type"] == "WHAT_IF_COUNTERFACTUAL"
    assert res["intervention_type"] == "TRACK_CLOSURE"
    assert "recommendation" in res
