"""Simulation and Digital Twin Event Definitions."""
from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class EventType(str, Enum):
    TRAIN_CREATED = "TRAIN_CREATED"
    TRAIN_DEPARTED = "TRAIN_DEPARTED"
    TRAIN_ARRIVED = "TRAIN_ARRIVED"
    TRAIN_DELAYED = "TRAIN_DELAYED"
    TRAIN_STOPPED = "TRAIN_STOPPED"
    TRAIN_SPEED_CHANGED = "TRAIN_SPEED_CHANGED"
    SIGNAL_CHANGED = "SIGNAL_CHANGED"
    SWITCH_THROWN = "SWITCH_THROWN"
    PLATFORM_ASSIGNED = "PLATFORM_ASSIGNED"
    PLATFORM_OCCUPIED = "PLATFORM_OCCUPIED"
    PLATFORM_RELEASED = "PLATFORM_RELEASED"
    TRACK_OCCUPIED = "TRACK_OCCUPIED"
    TRACK_RELEASED = "TRACK_RELEASED"
    CONFLICT_DETECTED = "CONFLICT_DETECTED"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"
    ROUTE_CHANGED = "ROUTE_CHANGED"
    SCHEDULE_CHANGED = "SCHEDULE_CHANGED"
    MAINTENANCE_STARTED = "MAINTENANCE_STARTED"
    MAINTENANCE_COMPLETED = "MAINTENANCE_COMPLETED"
    EMERGENCY_DECLARED = "EMERGENCY_DECLARED"
    OPTIMIZATION_COMPLETED = "OPTIMIZATION_COMPLETED"
    TELEMETRY_UPDATED = "TELEMETRY_UPDATED"

class SimEvent(BaseModel):
    id: Optional[str] = None
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sim_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    entity_id: str
    entity_type: str  # TRAIN, TRACK, PLATFORM, SIGNAL, SWITCH, JUNCTION
    payload: Dict[str, Any] = Field(default_factory=dict)
