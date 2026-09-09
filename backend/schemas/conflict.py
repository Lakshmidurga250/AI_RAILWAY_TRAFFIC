"""Conflict schemas."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ConflictResponse(BaseModel):
    id: str
    conflict_type: str
    severity: str
    status: str
    location_type: str
    location_id: str
    primary_train_id: str
    secondary_train_id: Optional[str] = None
    detected_at: datetime
    predicted_time: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    cause: str
    predicted_impact: Optional[str] = None
    recommended_action: Optional[str] = None
    resolution_strategy: Optional[str] = None
    affected_resources: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class ConflictResolveRequest(BaseModel):
    conflict_id: str
    strategy: str  # HOLD_TRAIN, REROUTE, REASSIGN_PLATFORM, SPEED_REDUCTION
    action_parameters: Optional[Dict[str, Any]] = None

class DisruptionCreate(BaseModel):
    id: str
    disruption_type: str
    affected_resource_type: str  # TRACK, STATION, PLATFORM, JUNCTION, SIGNAL
    affected_resource_id: str
    severity: str = "HIGH"
    description: Optional[str] = None
    duration_minutes: int = 60

class DisruptionResponse(BaseModel):
    id: str
    disruption_type: str
    severity: str
    status: str
    affected_resource_type: str
    affected_resource_id: str
    description: Optional[str] = None
    start_time: datetime
    estimated_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    impact_summary: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DelayEventCreate(BaseModel):
    train_id: str
    delay_minutes: float
    delay_type: str = "PRIMARY"
    cause: str
    station_id: Optional[str] = None
    track_id: Optional[str] = None
    disruption_id: Optional[str] = None

class DelayEventResponse(BaseModel):
    id: int
    train_id: str
    delay_minutes: float
    delay_type: str
    cause: str
    station_id: Optional[str] = None
    track_id: Optional[str] = None
    disruption_id: Optional[str] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)

