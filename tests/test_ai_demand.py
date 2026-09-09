"""Passenger Demand Forecasting Tests."""
from ai.demand_prediction.predictor import DemandPredictor

def test_demand_prediction():
    res = DemandPredictor.predict_station_demand(station_id="ST_CENTRAL", horizon_hours=24)
    assert res["station_id"] == "ST_CENTRAL"
    assert len(res["hourly_forecast"]) == 24
    assert "peak_hours" in res
    assert len(res["peak_hours"]) > 0
    assert "confidence_interval" in res
