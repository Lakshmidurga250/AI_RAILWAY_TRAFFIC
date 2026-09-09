"""AI and Machine Learning Models: ModelRegistry, Predictions, Demand, Congestion."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from backend.app.database import Base

class AIModelRegistry(Base):
    __tablename__ = "ai_models"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    task = Column(String(50), nullable=False)  # DELAY_PREDICTION, CONGESTION_PREDICTION, DEMAND_PREDICTION, RL_POLICY
    algorithm = Column(String(50), nullable=False)  # RANDOM_FOREST, GRADIENT_BOOSTING, LINEAR_REGRESSION, LSTM, PPO, DQN
    version = Column(String(20), default="1.0.0")
    status = Column(String(30), default="ACTIVE")  # TRAINING, VALIDATED, ACTIVE, RETIRED, FAILED
    metrics = Column(JSON, nullable=True)  # MAE, RMSE, R2, accuracy, reward
    feature_names = Column(JSON, nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    artifact_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), nullable=False, index=True)
    prediction_type = Column(String(50), nullable=False)  # DELAY, CONGESTION, DEMAND
    target_entity_id = Column(String(50), nullable=False, index=True)  # train_id, station_id, track_id
    horizon_minutes = Column(Integer, default=15)
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.85)
    contributing_factors = Column(JSON, nullable=True)  # Feature importance / explanation
    actual_value = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
