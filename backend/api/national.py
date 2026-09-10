"""National Control Room API endpoints.

Exposes national-scale KPIs, alert management, fleet utilisation, and
cross-zonal handoff data consumed by the NCR frontend dashboard.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from simulation.national_scale.national_coordinator import national_coordinator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/national", tags=["National Control Room"])


# ─── Request schemas ──────────────────────────────────────────────────────────

class CrossZonalRouteRequest(BaseModel):
    train_id: str
    origin_station: str
    destination_station: str
    train_type: str = "EXPRESS"
    estimated_distance_km: float = 0.0


class HandoffRequest(BaseModel):
    train_id: str
    at_station: str
    delay_minutes: float = 0.0
    passenger_km: float = 0.0
    energy_kwh: float = 0.0


class AlertRequest(BaseModel):
    alert_type: str
    zone_code: str
    description: str
    severity: str = "HIGH"
    station_id: Optional[str] = None
    affected_train_ids: list[str] = []


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/dashboard", summary="NCR full dashboard payload")
async def get_ncr_dashboard() -> Dict[str, Any]:
    """
    Return the complete National Control Room dashboard:
    national KPIs, per-zone breakdown, active alerts, fleet utilisation,
    and recent inter-zonal handoff log.
    """
    try:
        return national_coordinator.get_ncr_dashboard()
    except Exception as exc:
        logger.exception("NCR dashboard error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/kpi", summary="National KPI summary")
async def get_national_kpi() -> Dict[str, Any]:
    """Aggregate KPIs for all active zones."""
    return national_coordinator.zone_manager.get_national_kpi()


@router.get("/kpi/zone/{zone_code}", summary="Single zone KPI")
async def get_zone_kpi(zone_code: str) -> Dict[str, Any]:
    """KPI snapshot for a specific railway zone."""
    data = national_coordinator.zone_manager.get_zone_kpi(zone_code.upper())
    if data is None:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_code}' not found")
    return data


@router.get("/alerts", summary="Active national alerts")
async def get_national_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL|HIGH|MEDIUM|LOW")
) -> list[Dict[str, Any]]:
    """Return all unresolved national alerts, optionally filtered by severity."""
    return national_coordinator.get_active_alerts(severity=severity)


@router.post("/alerts", status_code=201, summary="Raise a national alert")
async def raise_alert(req: AlertRequest) -> Dict[str, Any]:
    """Create and broadcast a new national operational alert."""
    alert = national_coordinator.raise_alert(
        alert_type=req.alert_type,
        zone_code=req.zone_code.upper(),
        description=req.description,
        severity=req.severity.upper(),
        station_id=req.station_id,
        affected_train_ids=req.affected_train_ids,
    )
    return alert.to_dict()


@router.patch("/alerts/{alert_id}/resolve", summary="Resolve an alert")
async def resolve_alert(alert_id: str) -> Dict[str, Any]:
    """Mark a national alert as resolved."""
    success = national_coordinator.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return {"status": "resolved", "alert_id": alert_id}


@router.get("/fleet", summary="Fleet utilisation breakdown")
async def get_fleet_utilisation() -> list[Dict[str, Any]]:
    """Return rolling-stock utilisation records for all fleet types."""
    return national_coordinator.get_fleet_utilisation()


@router.post("/routes/plan", status_code=201, summary="Plan a cross-zonal route")
async def plan_cross_zonal_route(req: CrossZonalRouteRequest) -> Dict[str, Any]:
    """
    Plan a cross-zonal route for a long-distance train.
    Returns the route sequence including intermediate zones and boundary stations.
    """
    route = national_coordinator.plan_cross_zonal_route(
        train_id=req.train_id,
        origin_station=req.origin_station,
        destination_station=req.destination_station,
        train_type=req.train_type.upper(),
        estimated_distance_km=req.estimated_distance_km,
    )
    return {
        "route_id": route.route_id,
        "train_id": route.train_id,
        "origin_station": route.origin_station,
        "destination_station": route.destination_station,
        "origin_zone": route.origin_zone,
        "destination_zone": route.destination_zone,
        "intermediate_zones": route.intermediate_zones,
        "boundary_handoff_stations": route.boundary_handoff_stations,
        "priority": route.priority,
        "estimated_distance_km": route.estimated_distance_km,
        "estimated_duration_hours": route.estimated_duration_hours,
    }


@router.post("/routes/handoff", summary="Process inter-zonal handoff")
async def process_handoff(req: HandoffRequest) -> Dict[str, Any]:
    """
    Process a zonal boundary crossing for a train.
    Updates zone statistics and emits a structured handoff event.
    """
    result = national_coordinator.process_handoff(
        train_id=req.train_id,
        at_station=req.at_station,
        delay_minutes=req.delay_minutes,
        passenger_km=req.passenger_km,
        energy_kwh=req.energy_kwh,
    )
    if result is None:
        raise HTTPException(
            status_code=400,
            detail=f"No route registered for train '{req.train_id}', or train already at final zone."
        )
    return result


@router.get("/routes/{train_id}/status", summary="Train route status")
async def get_route_status(train_id: str) -> Dict[str, Any]:
    """Return the current cross-zonal route status for a train."""
    status = national_coordinator.get_route_status(train_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"No active route for train '{train_id}'")
    return status


@router.get("/alerts/zones", summary="Alert-zone list")
async def get_alert_zones(
    threshold: float = Query(80.0, description="Punctuality % below which zones are flagged")
) -> list[Dict[str, Any]]:
    """Return zones whose punctuality has fallen below the given threshold."""
    return national_coordinator.zone_manager.get_alert_zones(punctuality_threshold=threshold)


@router.get("/handoffs/log", summary="Recent inter-zonal handoff log")
async def get_handoff_log(
    limit: int = Query(50, ge=1, le=200)
) -> list[Dict[str, Any]]:
    """Return the N most recent inter-zonal handoff events."""
    return national_coordinator.zone_manager.get_handoff_log(limit=limit)
