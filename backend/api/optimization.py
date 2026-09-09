"""Optimization API Endpoints."""
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from backend.services.optimization_service import OptimizationService
from backend.schemas.optimization import (
    RouteOptimizationRequest, RouteOptimizationResponse,
    PlatformOptimizationRequest, PlatformOptimizationResponse,
    ReschedulingRequest, ReschedulingResponse,
    EnergyOptimizationRequest, EnergyOptimizationResponse
)
from backend.services.ai_service import AIService

router = APIRouter(prefix="/optimization", tags=["Optimization"])

@router.post("/route", response_model=RouteOptimizationResponse)
def optimize_route(req: RouteOptimizationRequest):
    return OptimizationService.optimize_route(
        origin_station_id=req.origin_station_id,
        destination_station_id=req.destination_station_id,
        algorithm=req.algorithm,
        train_id=req.train_id
    )

@router.post("/platform", response_model=PlatformOptimizationResponse)
def optimize_platform(req: PlatformOptimizationRequest):
    res = OptimizationService.optimize_platform(
        station_id=req.station_id,
        train_id=req.train_id
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/schedule")
def optimize_schedule():
    return OptimizationService.optimize_schedule()

@router.post("/reschedule", response_model=ReschedulingResponse)
def dynamic_reschedule(req: ReschedulingRequest):
    return OptimizationService.dynamic_reschedule(
        scenario_type=req.scenario_type,
        affected_resource_id=req.affected_resource_id,
        duration_minutes=req.duration_minutes
    )

@router.post("/energy", response_model=EnergyOptimizationResponse)
def optimize_energy_profile(req: EnergyOptimizationRequest):
    return AIService.optimize_energy(req.train_id)

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: str):
    res = OptimizationService.resolve_active_conflict(conflict_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res
