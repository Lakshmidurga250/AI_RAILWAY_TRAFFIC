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
