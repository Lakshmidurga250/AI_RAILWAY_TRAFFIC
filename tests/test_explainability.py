"""Explainable AI (XAI) Engine Tests."""
from ai.explainability.explainer import ExplainabilityEngine

def test_explain_delay_prediction():
    features = {
        "track_congestion_index": 0.8,
        "preceding_train_delay_min": 6.0,
        "platform_occupancy_rate": 0.7,
        "weather_severity": 1.0,
        "actual_dwell_sec": 160.0
    }
    res = ExplainabilityEngine.explain_delay_prediction(predicted_delay_min=12.4, features_dict=features)
    assert "feature_attributions" in res
    assert len(res["feature_attributions"]) > 0
    assert "explanation_narrative" in res
    assert "track congestion index" in res["explanation_narrative"]

def test_counterfactual_recommendations():
    features = {
        "track_congestion_index": 0.75,
        "preceding_train_delay_min": 5.5,
        "actual_dwell_sec": 190.0
    }
    cf = ExplainabilityEngine.generate_counterfactual(current_delay=14.0, features_dict=features, target_delay=3.0)
    assert not cf.get("target_achieved", False)
    assert cf["gap_to_close_minutes"] == 11.0
    assert len(cf["counterfactual_actions"]) >= 2
