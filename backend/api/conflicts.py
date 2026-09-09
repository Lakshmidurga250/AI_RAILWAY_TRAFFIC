"""Conflicts, Disruptions, and Delay Management API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.schemas.conflict import (
    ConflictResponse,
    DisruptionCreate,
    DisruptionResponse,
    DelayEventCreate,
    DelayEventResponse
)
from backend.services.disruption_service import DisruptionService
from backend.app.dependencies import get_current_user
from backend.models.user import User
from simulation.engine.simulator import sim_engine

router = APIRouter(prefix="/conflicts", tags=["Conflicts & Disruptions"])

@router.get("", response_model=List[ConflictResponse])
def list_active_conflicts():
    """List currently active physical conflicts detected by Arbiter."""
    with sim_engine.step_lock:
        return [c.to_dict() for c in sim_engine.conflict_detector.active_conflicts.values()]

@router.get("/history", response_model=List[ConflictResponse])
def list_resolved_conflicts():
    """List resolved conflicts from simulation history buffer."""
    with sim_engine.step_lock:
        return [c.to_dict() for c in sim_engine.conflict_detector.resolved_conflicts]

# Disruptions Management
@router.get("/disruptions", response_model=List[DisruptionResponse])
def list_disruptions(
    active_only: bool = Query(True, description="Filter for only active disruptions"),
    db: Session = Depends(get_db)
):
    """List operational disruptions (track closures, signal failures, severe weather)."""
    return DisruptionService.list_disruptions(active_only=active_only, db=db)

@router.post("/disruptions", response_model=DisruptionResponse, status_code=status.HTTP_201_CREATED)
def create_disruption(
    payload: DisruptionCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inject a new disruption into the digital twin, calculate impact, and propagate blocks."""
    if current_user and not current_user.has_permission("tracks:write"):
        raise HTTPException(status_code=403, detail="Missing required permission: tracks:write")

    disruption = DisruptionService.register_disruption(
        disruption_id=payload.id,
        disruption_type=payload.disruption_type,
        affected_resource_type=payload.affected_resource_type,
        affected_resource_id=payload.affected_resource_id,
        severity=payload.severity,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        db=db
    )
    return disruption

@router.post("/disruptions/{disruption_id}/resolve", response_model=DisruptionResponse)
def resolve_disruption(
    disruption_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a disruption as resolved and clear track/signal blockages."""
    if current_user and not current_user.has_permission("tracks:write"):
        raise HTTPException(status_code=403, detail="Missing required permission: tracks:write")

    resolved = DisruptionService.resolve_disruption(disruption_id, db=db)
    if not resolved:
        raise HTTPException(status_code=404, detail=f"Disruption '{disruption_id}' not found")
    return resolved

# Delay Events
@router.get("/delays", response_model=List[DelayEventResponse])
def list_delay_events(
    train_id: Optional[str] = Query(None, description="Filter delays by train ID"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Fetch time-stamped delay events across the network."""
    return DisruptionService.list_delays(train_id=train_id, limit=limit, db=db)

@router.post("/delays", response_model=DelayEventResponse, status_code=status.HTTP_201_CREATED)
def record_delay_event(
    payload: DelayEventCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a granular delay incident for a train."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing required permission: trains:write")

    return DisruptionService.log_delay_event(
        train_id=payload.train_id,
        delay_minutes=payload.delay_minutes,
        delay_type=payload.delay_type,
        cause=payload.cause,
        station_id=payload.station_id,
        track_id=payload.track_id,
        disruption_id=payload.disruption_id,
        db=db
    )
