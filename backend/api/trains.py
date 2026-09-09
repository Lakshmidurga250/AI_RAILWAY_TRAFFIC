"""Train Fleet Management API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.train_service import TrainService
from backend.schemas.train import TrainResponse

router = APIRouter(prefix="/trains", tags=["Trains"])

@router.get("", response_model=List[TrainResponse])
def list_trains(status: Optional[str] = Query(None, description="Filter by operational status")):
    return TrainService.list_trains(status=status)

@router.get("/{train_id}", response_model=TrainResponse)
def get_train(train_id: str):
    train = TrainService.get_train(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return train

@router.post("/{train_id}/priority")
def set_priority(train_id: str, priority: int = Query(..., ge=1, le=10)):
    success = TrainService.update_train_priority(train_id, priority)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"message": f"Updated train {train_id} priority to {priority}", "status": "SUCCESS"}

@router.post("/{train_id}/speed")
def set_speed(train_id: str, target_speed_kmh: float = Query(..., ge=0, le=300)):
    success = TrainService.update_train_speed(train_id, target_speed_kmh)
    if not success:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    return {"message": f"Updated train {train_id} target speed to {target_speed_kmh} km/h", "status": "SUCCESS"}
