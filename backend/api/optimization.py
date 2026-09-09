"""Optimization API Endpoints with Metaheuristics and Audit Trails."""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.services.optimization_service import OptimizationService
from backend.schemas.optimization import (
    RouteOptimizationRequest, RouteOptimizationResponse,
    PlatformOptimizationRequest, PlatformOptimizationResponse,
    ReschedulingRequest, ReschedulingResponse,
    EnergyOptimizationRequest, EnergyOptimizationResponse,
    OptimizationRunResponse
)
from backend.services.ai_service import AIService

router = APIRouter(prefix="/optimization", tags=["Optimization"])

@router.post("/route", response_model=RouteOptimizationResponse)
def optimize_route(req: RouteOptimizationRequest, db: Session = Depends(get_db)):
    """Compute optimal train route using Dijkstra, A*, Floyd-Warshall, Pareto, GA, PSO, or SA."""
    return OptimizationService.optimize_route(
        origin_station_id=req.origin_station_id,
        destination_station_id=req.destination_station_id,
        algorithm=req.algorithm,
        train_id=req.train_id,
        db=db
    )

@router.post("/platform", response_model=PlatformOptimizationResponse)
def optimize_platform(req: PlatformOptimizationRequest, db: Session = Depends(get_db)):
    """Assign optimal station platform avoiding contentions."""
    res = OptimizationService.optimize_platform(
        station_id=req.station_id,
        train_id=req.train_id,
        db=db
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/schedule")
def optimize_schedule(db: Session = Depends(get_db)):
    """Optimize macroscopic corridor timetable with conflict-free headways."""
    return OptimizationService.optimize_schedule(db=db)

@router.post("/reschedule", response_model=ReschedulingResponse)
def dynamic_reschedule(req: ReschedulingRequest, db: Session = Depends(get_db)):
    """Dynamically reschedule active trains around a track disruption."""
    return OptimizationService.dynamic_reschedule(
        scenario_type=req.scenario_type,
        affected_resource_id=req.affected_resource_id,
        duration_minutes=req.duration_minutes,
        db=db
    )

@router.post("/energy", response_model=EnergyOptimizationResponse)
def optimize_energy_profile(req: EnergyOptimizationRequest):
    """Generate eco-driving speed profile with coasting phases."""
    return AIService.optimize_energy(req.train_id)

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: str):
    """Execute automated conflict resolution strategy."""
    res = OptimizationService.resolve_active_conflict(conflict_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/runs", response_model=List[OptimizationRunResponse])
def list_optimization_runs(
    limit: int = Query(50, ge=1, le=200),
    optimization_type: Optional[str] = Query(None, description="Filter by ROUTING, SCHEDULING, PLATFORM, RESCHEDULING"),
    db: Session = Depends(get_db)
):
    """Retrieve historical optimization runs with execution time and savings metrics."""
    return OptimizationService.list_optimization_runs(limit=limit, optimization_type=optimization_type, db=db)
