"""Delay Prediction Machine Learning Pipeline Tests."""
import numpy as np
from ai.delay_prediction.predictor import DelayPredictor
from ai.features.engineering import FeatureEngineer
from ai.data.synthetic import synthetic_generator

def test_delay_predictor_training():
    predictor = DelayPredictor(model_type="GRADIENT_BOOSTING")
    df = synthetic_generator.generate_delay_training_dataset(num_samples=250)
    predictor.train_models(df)
    
    assert predictor.is_trained
    assert 5 in predictor.models
    assert 15 in predictor.models
    assert 60 in predictor.models
    assert "RMSE" in predictor.metrics[15]
    assert predictor.metrics[15]["RMSE"] > 0

def test_delay_inference_across_horizons():
    predictor = DelayPredictor(model_type="GRADIENT_BOOSTING")
    df = synthetic_generator.generate_delay_training_dataset(num_samples=200)
    predictor.train_models(df)

    # Mock feature array
    mock_features = np.zeros((1, len(FeatureEngineer.FEATURE_NAMES)), dtype=np.float32)
    mock_features[0, 0] = 5.0  # current delay 5 min
    mock_features[0, 5] = 0.8  # high congestion
    
    res = predictor.predict(mock_features, horizon_minutes=15, current_delay=5.0)
    assert "predicted_delay_minutes" in res
    assert res["predicted_delay_minutes"] >= 0.0
    assert "confidence" in res
    assert 0.0 <= res["confidence"] <= 1.0
    assert "contributing_factors" in res
    assert len(res["contributing_factors"]) > 0
