"""AI Model Registry and Lifecycle Management."""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class ModelArtifact(BaseModel):
    id: str
    name: str
    task: str  # DELAY_PREDICTION, CONGESTION_PREDICTION, DEMAND_PREDICTION, RL_DISPATCH
    algorithm: str
    version: str
    status: str = "ACTIVE"  # TRAINING, VALIDATED, ACTIVE, RETIRED, FAILED
    metrics: Dict[str, float] = Field(default_factory=dict)
    feature_names: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ModelRegistry:
    """Manages active and historical ML and RL models across the platform."""

    def __init__(self):
        self._models: Dict[str, ModelArtifact] = {}
        self._initialize_default_registry()

    def _initialize_default_registry(self):
        """Seed registry with production-ready default models."""
        defaults = [
            ModelArtifact(
                id="MOD_DELAY_GBM_V1",
                name="Corridor Multi-Horizon Delay Predictor",
                task="DELAY_PREDICTION",
                algorithm="GRADIENT_BOOSTING",
                version="1.2.0",
                status="ACTIVE",
                metrics={"MAE": 1.12, "RMSE": 1.64, "R2": 0.88},
                feature_names=[
                    "historical_delay_min", "train_type_encoded", "scheduled_dwell_sec",
                    "actual_dwell_sec", "platform_occupancy_rate", "track_congestion_index",
                    "weather_severity", "passenger_load_factor", "preceding_train_delay_min"
                ],
                hyperparameters={"n_estimators": 80, "max_depth": 4, "learning_rate": 0.08}
            ),
            ModelArtifact(
                id="MOD_CONGESTION_RF_V1",
                name="Network Bottleneck & Congestion Forecaster",
                task="CONGESTION_PREDICTION",
                algorithm="RANDOM_FOREST",
                version="1.1.0",
                status="ACTIVE",
                metrics={"Accuracy": 0.93, "F1_Score": 0.91, "ROC_AUC": 0.96},
                feature_names=["occupancy_rate", "junction_load", "track_density", "signal_blocks_occupied"],
                hyperparameters={"n_estimators": 100, "max_depth": 8}
            ),
            ModelArtifact(
                id="MOD_DEMAND_TS_V1",
                name="Hourly Passenger Flow & Surge Forecaster",
                task="DEMAND_PREDICTION",
                algorithm="SEASONAL_REGRESSION",
                version="2.0.1",
                status="ACTIVE",
                metrics={"MAPE": 6.8, "RMSE": 42.5},
                feature_names=["hour", "day_of_week", "weather_factor", "historical_mean"],
                hyperparameters={"seasonality_periods": 24}
            ),
            ModelArtifact(
                id="MOD_RL_DISPATCH_DQN_V1",
                name="Autonomous Dispatch & Conflict Resolution Policy",
                task="RL_DISPATCH",
                algorithm="DEEP_Q_NETWORK",
                version="1.0.0",
                status="ACTIVE",
                metrics={"Mean_Reward": 84.5, "Conflict_Reduction_Pct": 78.2},
                feature_names=["train_states", "track_occupancy", "network_metrics"],
                hyperparameters={"gamma": 0.95, "lr": 0.001, "epsilon_min": 0.05}
            )
        ]
        for m in defaults:
            self._models[m.id] = m

    def list_models(self, task: Optional[str] = None) -> List[ModelArtifact]:
        """List registered models, optionally filtered by task."""
        models = list(self._models.values())
        if task:
            models = [m for m in models if m.task == task]
        return models

    def get_model(self, model_id: str) -> Optional[ModelArtifact]:
        return self._models.get(model_id)

    def register_model(self, artifact: ModelArtifact):
        self._models[artifact.id] = artifact

    def update_status(self, model_id: str, new_status: str) -> bool:
        if model_id in self._models:
            self._models[model_id].status = new_status
            return True
        return False

model_registry = ModelRegistry()
