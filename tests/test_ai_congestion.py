"""Congestion Prediction Tests."""
from ai.congestion_prediction.predictor import CongestionPredictor
from simulation.network.loader import create_corridor_network

def test_congestion_prediction():
    net = create_corridor_network()
    res = CongestionPredictor.predict_congestion(
        resource_type="STATION",
        resource_id="ST_CENTRAL",
        network=net,
        horizon_minutes=15
    )
    assert "congestion_score" in res
    assert 0.0 <= res["congestion_score"] <= 1.0
    assert res["congestion_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert "recommendations" in res
    assert len(res["recommendations"]) > 0
