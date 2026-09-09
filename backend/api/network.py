"""Railway Infrastructure Network API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.network_service import NetworkService
from backend.schemas.network import TrackSchema, SignalSchema, NetworkGraphResponse

router = APIRouter(prefix="/network", tags=["Network Infrastructure"])

@router.get("/graph", response_model=NetworkGraphResponse)
def get_network_graph():
    return NetworkService.get_network_graph()

@router.get("/tracks", response_model=List[TrackSchema])
def list_tracks():
    return NetworkService.get_tracks()

@router.get("/signals", response_model=List[SignalSchema])
def list_signals():
    return NetworkService.get_signals()

@router.put("/tracks/{track_id}/status")
def update_track_status(
    track_id: str,
    status: str = Query(..., description="CLEAR, OCCUPIED, MAINTENANCE, BLOCKED, SPEED_RESTRICTED"),
    speed_restriction_kmh: Optional[float] = Query(None)
):
    success = NetworkService.update_track_status(track_id, status, speed_restriction_kmh)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to update track {track_id}")
    return {"message": f"Track {track_id} status updated to {status}", "status": "SUCCESS"}
