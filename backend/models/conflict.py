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

class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(String(50), primary_key=True, index=True)
    disruption_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="HIGH", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), default="ACTIVE", index=True)  # ACTIVE, MITIGATING, RESOLVED, CANCELLED
    affected_resource_type = Column(String(30), nullable=False)  # TRACK, STATION, PLATFORM, JUNCTION, SIGNAL
    affected_resource_id = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    estimated_end_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    impact_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class DelayEvent(Base):
    __tablename__ = "delay_events"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id", ondelete="CASCADE"), nullable=False, index=True)
    station_id = Column(String(50), nullable=True)
    track_id = Column(String(50), nullable=True)
    delay_minutes = Column(Float, nullable=False, default=0.0)
    delay_type = Column(String(50), default="PRIMARY", index=True)  # PRIMARY, REACTIONARY, WEATHER, INFRASTRUCTURE
    cause = Column(Text, nullable=False)
    disruption_id = Column(String(50), ForeignKey("disruptions.id"), nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
