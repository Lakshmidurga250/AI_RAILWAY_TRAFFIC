"""Multi-Horizon Train Delay Prediction Pipeline."""
import os
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from ai.data.synthetic import synthetic_generator
from ai.features.engineering import FeatureEngineer

class DelayPredictor:
    """Predicts future train delays across 5m, 10m, 15m, 30m, and 60m horizons."""

    HORIZONS = [5, 10, 15, 30, 60]
    
    def __init__(self, model_type: str = "GRADIENT_BOOSTING"):
        self.model_type = model_type
        self.models: Dict[int, Any] = {}
        self.metrics: Dict[int, Dict[str, float]] = {}
        self.feature_importances: Dict[int, Dict[str, float]] = {}
        self.version = "1.2.0"
        self.is_trained = False

    def train_models(self, df: Optional[pd.DataFrame] = None):
        """Train distinct regressors for each prediction horizon."""
        if df is None:
            df = synthetic_generator.generate_delay_training_dataset(num_samples=2500)

        feature_cols = FeatureEngineer.FEATURE_NAMES
        X = df[feature_cols].values

        for h in self.HORIZONS:
            target_col = f"delay_{h}m"
            y = df[target_col].values

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            if self.model_type == "GRADIENT_BOOSTING":
                model = GradientBoostingRegressor(n_estimators=80, max_depth=4, learning_rate=0.08, random_state=42)
            elif self.model_type == "RANDOM_FOREST":
                model = RandomForestRegressor(n_estimators=70, max_depth=6, random_state=42, n_jobs=-1)
            else:
                model = Ridge(alpha=1.0)

            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            mae = float(mean_absolute_error(y_test, y_pred))
            mse = float(mean_squared_error(y_test, y_pred))
            rmse = float(math.sqrt(mse))
            r2 = float(r2_score(y_test, y_pred))

            self.models[h] = model
            self.metrics[h] = {"MAE": round(mae, 3), "MSE": round(mse, 3), "RMSE": round(rmse, 3), "R2": round(r2, 3)}

            # Feature importances
            if hasattr(model, "feature_importances_"):
                importances = {name: round(float(imp), 4) for name, imp in zip(feature_cols, model.feature_importances_)}
            else:
                importances = {name: 0.1 for name in feature_cols}
            self.feature_importances[h] = importances

        self.is_trained = True

    def predict(
        self,
        features_array: np.ndarray,
        horizon_minutes: int = 15,
        current_delay: float = 0.0
    ) -> Dict[str, Any]:
        """Inference for a single train across requested horizon."""
        if not self.is_trained:
            self.train_models()

        # Find closest available horizon model
        chosen_h = min(self.HORIZONS, key=lambda x: abs(x - horizon_minutes))
        model = self.models.get(chosen_h)

        if not model:
            predicted_val = max(0.0, current_delay + (horizon_minutes / 15.0) * 0.5)
        else:
            pred = float(model.predict(features_array)[0])
            predicted_val = max(0.0, pred)

        # Compute confidence: higher confidence for shorter horizon and low error
        rmse = self.metrics.get(chosen_h, {}).get("RMSE", 1.5)
        confidence = max(0.55, min(0.96, 1.0 - (rmse / max(5.0, predicted_val + 5.0))))

        # Identify top contributing factors
        importances = self.feature_importances.get(chosen_h, {})
        top_factors = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:4]
        contributing_factors = [
            {"factor": factor, "importance": round(imp, 3), "impact": "High" if imp > 0.15 else "Moderate"}
            for factor, imp in top_factors
        ]

        # Natural language explanation
        risk_level = "LOW"
        if predicted_val > 15.0:
            risk_level = "SEVERE"
        elif predicted_val > 8.0:
            risk_level = "HIGH"
        elif predicted_val > 3.0:
            risk_level = "MODERATE"

        top_names = [f["factor"].replace("_", " ") for f in contributing_factors[:2]]
        explanation = (
            f"Forecasts {predicted_val:.1f} min delay at {horizon_minutes}m horizon (Risk: {risk_level}). "
            f"Primary contributors: {', '.join(top_names)}."
        )

        return {
            "horizon_minutes": horizon_minutes,
            "predicted_delay_minutes": round(predicted_val, 2),
            "confidence": round(confidence, 2),
            "risk_level": risk_level,
            "contributing_factors": contributing_factors,
            "explanation": explanation,
            "model_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

# Global singleton predictor
delay_predictor = DelayPredictor()
