"""Conflict Models: Conflict Detection, Severity, Resolution Recommendations."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from backend.app.database import Base

class Conflict(Base):
    __tablename__ = "conflicts"
    
    id = Column(String(50), primary_key=True, index=True)
    conflict_type = Column(String(50), nullable=False, index=True)  # SAME_TRACK, HEADWAY, JUNCTION_OVERLAP, PLATFORM_CONTENTION, CROSSING
    severity = Column(String(20), default="MEDIUM", index=True)  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(20), default="ACTIVE", index=True)  # ACTIVE, RESOLVED, MITIGATED, DISMISSED
    
    location_type = Column(String(30), nullable=False)  # TRACK, JUNCTION, PLATFORM, STATION
    location_id = Column(String(50), nullable=False)
    
    primary_train_id = Column(String(50), nullable=False, index=True)
    secondary_train_id = Column(String(50), nullable=True, index=True)
    
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    predicted_time = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    cause = Column(Text, nullable=False)
    predicted_impact = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    resolution_strategy = Column(String(50), nullable=True)  # HOLD_TRAIN, REROUTE, PLATFORM_REASSIGN, SPEED_ADJUSTMENT
    affected_resources = Column(JSON, nullable=True)
