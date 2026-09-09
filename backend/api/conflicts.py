"""Conflicts API Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from backend.schemas.conflict import ConflictResponse
from simulation.engine.simulator import sim_engine

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])

@router.get("", response_model=List[ConflictResponse])
def list_active_conflicts():
    with sim_engine.step_lock:
        return [c.to_dict() for c in sim_engine.conflict_detector.active_conflicts.values()]

@router.get("/history", response_model=List[ConflictResponse])
def list_resolved_conflicts():
    with sim_engine.step_lock:
        return [c.to_dict() for c in sim_engine.conflict_detector.resolved_conflicts]
