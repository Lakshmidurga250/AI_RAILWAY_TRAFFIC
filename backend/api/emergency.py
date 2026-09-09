"""Emergency Protocols & Kavach ATP API Endpoints."""
from typing import Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from simulation.safety.kavach import kavach_system
from simulation.engine.simulator import sim_engine

router = APIRouter(prefix="/emergency", tags=["Emergency Protocols & Kavach ATP"])

class EmergencyStopRequest(BaseModel):
    train_id: str
    reason: Optional[str] = "Dispatcher Emergency Halt"

class EmergencyReleaseRequest(BaseModel):
    train_id: str
    dispatcher_id: Optional[str] = "admin"

class SOSBroadcastRequest(BaseModel):
    track_id: str
    description: Optional[str] = "Track Obstruction / Hazard Alert"

@router.get("/status")
def get_kavach_status():
    """Retrieve real-time Kavach ATP safety telemetry and active emergency stops."""
    # Register live telemetry from active simulator trains
    for t in sim_engine.trains.values():
        kavach_system.register_telemetry(
            train_id=t.id,
            lat=getattr(t, "current_lat", 28.6139),
            lon=getattr(t, "current_lng", 77.2090),
            speed_kmh=getattr(t, "current_speed_kmh", 80.0),
            target_dist_m=getattr(t, "distance_to_signal", 1200.0),
            signal_aspect=getattr(t, "next_signal_aspect", "GREEN")
        )
    return kavach_system.get_status()

@router.post("/stop")
def trigger_emergency_stop(req: EmergencyStopRequest):
    """Actuate emergency pneumatic braking for a specific train."""
    # Also halt in simulator engine if present
    train = sim_engine.trains.get(req.train_id)
    if train:
        setattr(train, "current_speed_kmh", 0.0)
        setattr(train, "status", "EMERGENCY_STOP")
    result = kavach_system.trigger_emergency_brake(req.train_id, req.reason)
    return {"status": "SUCCESS", "detail": f"Emergency Brake applied to {req.train_id}", "event": result}

@router.post("/release")
def release_emergency_stop(req: EmergencyReleaseRequest):
    """Release emergency brake lock after safety validation."""
    result = kavach_system.release_emergency_brake(req.train_id, req.dispatcher_id)
    return {"status": "SUCCESS", "detail": f"Emergency Brake released for {req.train_id}", "event": result}

@router.post("/sos")
def broadcast_sos(req: SOSBroadcastRequest):
    """Broadcast SIL-4 SOS message across the corridor."""
    alert = kavach_system.trigger_sos_broadcast(req.track_id, req.description)
    return {"status": "BROADCASTED", "alert": alert.__dict__}
