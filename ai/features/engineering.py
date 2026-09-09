"""Feature Engineering Pipeline for Railway Prediction Models."""
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

class FeatureEngineer:
    """Extracts machine learning feature vectors from train and simulation state."""

    FEATURE_NAMES = [
        "historical_delay_min",
        "train_type_encoded",
        "scheduled_dwell_sec",
        "actual_dwell_sec",
        "platform_occupancy_rate",
        "track_congestion_index",
        "weather_severity",
        "passenger_load_factor",
        "preceding_train_delay_min",
        "time_of_day_hour",
        "day_of_week",
        "track_gradient_pct",
        "infrastructure_health_score"
    ]

    TRAIN_TYPE_MAP = {
        "HIGH_SPEED": 0,
        "INTERCITY": 1,
        "REGIONAL": 2,
        "COMMUTER": 3,
        "FREIGHT": 4
    }

    @classmethod
    def extract_features_from_train(
        cls,
        train,
        weather_severity: int = 0,
        platform_occupancy: float = 0.5,
        track_congestion: float = 0.3,
        preceding_delay: float = 0.0,
        infra_health: float = 0.95
    ) -> np.ndarray:
        """Construct feature vector from a live SimulationTrain instance."""
        now = datetime.now()
        hour = now.hour
        dow = now.weekday()
        
        type_code = cls.TRAIN_TYPE_MAP.get(train.train_type, 1)
        load_factor = (train.current_passengers / max(1, train.passenger_capacity)) if train.passenger_capacity > 0 else 0.5
        
        gradient = train.current_track.gradient_percent if train.current_track else 0.0
        
        feature_vector = [
            float(train.current_delay_minutes),
            float(type_code),
            120.0,  # scheduled dwell standard
            120.0 + max(0.0, (load_factor - 1.0) * 60.0),
            float(platform_occupancy),
            float(track_congestion),
            float(weather_severity),
            float(load_factor),
            float(preceding_delay),
            float(hour),
            float(dow),
            float(gradient),
            float(infra_health)
        ]
        return np.array([feature_vector], dtype=np.float32)

    @classmethod
    def get_feature_names(cls) -> List[str]:
        return cls.FEATURE_NAMES.copy()
