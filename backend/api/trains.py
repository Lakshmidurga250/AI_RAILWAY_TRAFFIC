from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.services.train_service import TrainService
from backend.schemas.train import (
    TrainResponse,
    TrainCreate,
    TrainUpdate,
    TrainStatusHistoryResponse,
    TrainPositionResponse
)
from backend.app.dependencies import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/trains", tags=["Trains"])

@router.get("", response_model=List[TrainResponse])
def list_trains(
    status: Optional[str] = Query(None, description="Filter by operational status"),
    db: Session = Depends(get_db)
):
    """List active train fleet with telemetry, status, and delays."""
    return TrainService.list_trains(status=status, db=db)

@router.post("", response_model=TrainResponse, status_code=status.HTTP_201_CREATED)
def create_train(
    train_in: TrainCreate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new timetabled train in the system."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:write")
    existing = TrainService.get_train(train_in.id, db=db)
    if existing:
        raise HTTPException(status_code=400, detail=f"Train ID '{train_in.id}' already exists")
    created = TrainService.create_train(train_in, db=db)
    return TrainService.get_train(created.id, db=db)

@router.get("/{train_id}", response_model=TrainResponse)
def get_train(train_id: str, db: Session = Depends(get_db)):
    """Fetch details, position, and schedule for a single train."""
    train = TrainService.get_train(train_id, db=db)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return train

@router.put("/{train_id}", response_model=TrainResponse)
def update_train(
    train_id: str,
    train_update: TrainUpdate,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update train attributes such as priority, target speed, or operational status."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:write")
    updated = TrainService.update_train(train_id, train_update, db=db)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return updated

@router.delete("/{train_id}", status_code=status.HTTP_200_OK)
def delete_train(
    train_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel and remove a train from the fleet."""
    if current_user and not current_user.has_permission("trains:delete"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:delete")
    success = TrainService.delete_train(train_id, db=db)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"status": "SUCCESS", "message": f"Train {train_id} removed successfully"}

@router.post("/{train_id}/priority")
def set_priority(
    train_id: str,
    priority: int = Query(..., ge=1, le=10),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set train dispatching priority level (1=lowest, 10=emergency)."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:write")
    success = TrainService.update_train_priority(train_id, priority, db=db)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"message": f"Updated train {train_id} priority to {priority}", "status": "SUCCESS"}

@router.post("/{train_id}/speed")
def set_speed(
    train_id: str,
    target_speed_kmh: float = Query(..., ge=0, le=300),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Command target speed on an active train."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:write")
    success = TrainService.update_train_speed(train_id, target_speed_kmh)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"message": f"Updated train {train_id} target speed to {target_speed_kmh} km/h", "status": "SUCCESS"}

@router.post("/{train_id}/emergency-stop")
def emergency_stop(
    train_id: str,
    reason: str = Query("EMERGENCY_BRAKE_ACTIVATED", description="Reason for stopping"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger immediate emergency brake on train, bringing speed to 0 km/h."""
    if current_user and not current_user.has_permission("trains:write"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:write")
    success = TrainService.emergency_stop(train_id, reason=reason, db=db)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"status": "SUCCESS", "message": f"Emergency stop executed for train {train_id}"}

@router.get("/{train_id}/history", response_model=List[TrainStatusHistoryResponse])
def get_status_history(
    train_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query operational status transition history for a train."""
    if current_user and not current_user.has_permission("trains:read"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:read")
    return TrainService.get_status_history(train_id, limit=limit, db=db)

@router.get("/{train_id}/positions", response_model=List[TrainPositionResponse])
def get_positions_trail(
    train_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Query spatial telemetry trail breadcrumbs for GIS map visualization."""
    if current_user and not current_user.has_permission("trains:read"):
        raise HTTPException(status_code=403, detail="Missing permission: trains:read")
    return TrainService.get_positions_trail(train_id, limit=limit, db=db)
