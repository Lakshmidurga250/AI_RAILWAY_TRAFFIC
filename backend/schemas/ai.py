"""AI & Machine Learning Schemas."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DelayPredictionRequest(BaseModel):
    train_id: str
    horizon_minutes: int = 15  # 5, 10, 15, 30, 60

class DelayPredictionResponse(BaseModel):
    train_id: str
    train_number: str
    current_delay_minutes: float
    predicted_delay_minutes: float
    horizon_minutes: int
    confidence: float
    risk_level: str  # LOW, MODERATE, HIGH, SEVERE
    contributing_factors: List[Dict[str, Any]]
    explanation: str
    model_version: str
    timestamp: datetime

class CongestionPredictionRequest(BaseModel):
    resource_type: str = "STATION"  # STATION, TRACK, JUNCTION, CORRIDOR
    resource_id: str
    horizon_minutes: int = 15

class CongestionPredictionResponse(BaseModel):
    resource_type: str
    resource_id: str
    resource_name: str
    horizon_minutes: int
    congestion_score: float  # 0.0 to 1.0
    congestion_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    probability: float
    expected_duration_minutes: float
    affected_resources: List[str]
    recommendations: List[str]
    confidence: float
    timestamp: datetime

class DemandPredictionRequest(BaseModel):
    station_id: str
    horizon_hours: int = 24

class DemandPredictionResponse(BaseModel):
    station_id: str
    station_name: str
    current_occupancy: int
    capacity: int
    hourly_forecast: List[Dict[str, Any]]
    peak_hours: List[int]
    anomalies_detected: List[Dict[str, Any]]
    confidence_interval: Dict[str, float]
    timestamp: datetime

class AIModelCard(BaseModel):
    id: str
    name: str
    task: str
    algorithm: str
    version: str
    status: str
    dataset: Optional[str] = None
    metrics: Dict[str, float]
    feature_names: List[str]
    hyperparameters: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ModelTrainingRequest(BaseModel):
    hyperparameters: Optional[Dict[str, Any]] = None
    dataset: Optional[str] = None

class ModelEvaluationResponse(BaseModel):
    model_id: str
    name: str
    version: str
    task: str
    evaluation_timestamp: str
    dataset_evaluated: str
    current_metrics: Dict[str, float]
    baseline_metrics: Dict[str, Optional[float]]
    validation_status: str
    recommendation: str
