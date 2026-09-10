"""
National Railway Coordinator.

Orchestrates simultaneous simulation of all Indian Railway zones, manages
inter-zonal train handoffs, enforces national speed/load policy, and provides
a unified operations view for the National Control Room (NCR).

Architecture:
  NationalCoordinator
    ├── ZoneManager           (18 zones × KPI aggregation)
    ├── CrossZonalRouter      (finds inter-zone paths through boundary nodes)
    ├── NationalAlertBus      (broadcasts critical events to all zones)
    └── FleetUtilisationTracker (rolling-stock utilisation across all zones)
"""

from __future__ import annotations

import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from simulation.national_scale.zone_manager import ZoneManager, IndianRailwayZone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class CrossZonalRoute:
    """A train path that spans multiple railway zones."""
    route_id: str
    train_id: str
    origin_station: str
    destination_station: str
    origin_zone: str
    destination_zone: str
    intermediate_zones: List[str]
    boundary_handoff_stations: List[str]
    estimated_duration_hours: float
    estimated_distance_km: float
    priority: str = "NORMAL"   # NORMAL | EXPRESS | FREIGHT | RAJDHANI | VANDE

    def all_zones(self) -> List[str]:
        return [self.origin_zone] + self.intermediate_zones + [self.destination_zone]


@dataclass
class NationalAlert:
    """A critical or warning alert broadcast to the NCR and zone controllers."""
    alert_id: str
    alert_type: str        # DERAILMENT | SIGNAL_FAILURE | FLOOD | STRIKE | OVERLOAD
    severity: str          # CRITICAL | HIGH | MEDIUM | LOW
    zone_code: str
    station_id: Optional[str]
    description: str
    affected_train_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    resolved: bool = False

    def to_dict(self) -> Dict:
        return {
            "alert_id": self.alert_id,
            "type": self.alert_type,
            "severity": self.severity,
            "zone": self.zone_code,
            "station": self.station_id,
            "description": self.description,
            "affected_trains": self.affected_train_ids,
            "created_at": self.created_at,
            "resolved": self.resolved,
        }


@dataclass
class FleetUtilisationRecord:
    """Rolling-stock utilisation snapshot for NCR fleet dashboard."""
    fleet_type: str          # EMU | DIESEL_LOCO | ELECTRIC_LOCO | DEMU | VANDE
    total_units: int
    units_in_service: int
    units_under_maintenance: int
    units_reserved: int
    utilisation_pct: float
    avg_age_years: float

    def to_dict(self) -> Dict:
        return {
            "fleet_type": self.fleet_type,
            "total": self.total_units,
            "in_service": self.units_in_service,
            "maintenance": self.units_under_maintenance,
            "reserved": self.units_reserved,
            "utilisation_pct": round(self.utilisation_pct, 1),
            "avg_age_years": round(self.avg_age_years, 1),
        }


# ---------------------------------------------------------------------------
# National Coordinator
# ---------------------------------------------------------------------------

class NationalCoordinator:
    """
    Singleton-style top-level controller for the entire national rail network.

    Provides:
    - Cross-zonal route planning
    - Inter-zonal handoff orchestration
    - National alert broadcast and resolution
    - Fleet utilisation tracking
    - National-level KPI dashboard data
    """

    def __init__(self) -> None:
        self.zone_manager = ZoneManager()
        self._active_routes: Dict[str, CrossZonalRoute] = {}   # route_id -> route
        self._train_routes: Dict[str, str] = {}                 # train_id -> route_id
        self._alerts: Dict[str, NationalAlert] = {}
        self._alert_counter: int = 0
        self._fleet_data: Dict[str, FleetUtilisationRecord] = {}
        self._initialize_fleet_data()
        logger.info("NationalCoordinator online – managing %d zones.",
                    len(self.zone_manager.zones))

    # ------------------------------------------------------------------
    # Fleet initialisation (seed data)
    # ------------------------------------------------------------------

    def _initialize_fleet_data(self) -> None:
        seed = [
            ("WAP7_ELECTRIC_LOCO",  1200, 950, 180, 70,  92.5, 8.2),
            ("WDM3_DIESEL_LOCO",    1800, 1100, 500, 200, 76.3, 22.5),
            ("WAG9_FREIGHT_LOCO",   2400, 1900, 380, 120, 87.7, 11.0),
            ("ICF_COACH",          70000,55000,11000,4000, 84.6, 18.3),
            ("LHB_COACH",          45000,38000, 5000,2000, 88.9, 9.7),
            ("VANDE_BHARAT_EMU",     450,  390,   40,  20, 91.1, 2.8),
            ("MEMU_EMU",            1600, 1350,  180,  70, 90.6, 12.4),
            ("DEMU",                 900,  650,  200,  50, 79.4, 14.6),
        ]
        for (ftype, total, in_svc, maint, res, util, age) in seed:
            self._fleet_data[ftype] = FleetUtilisationRecord(
                fleet_type=ftype,
                total_units=total,
                units_in_service=in_svc,
                units_under_maintenance=maint,
                units_reserved=res,
                utilisation_pct=util,
                avg_age_years=age,
            )

    # ------------------------------------------------------------------
    # Cross-Zonal Route Planning
    # ------------------------------------------------------------------

    def plan_cross_zonal_route(
        self,
        train_id: str,
        origin_station: str,
        destination_station: str,
        train_type: str = "EXPRESS",
        estimated_distance_km: float = 0.0,
    ) -> CrossZonalRoute:
        """
        Plan a cross-zonal route for a long-distance train.

        Determines origin/destination zones from the boundary station registry,
        then sequences intermediate zones on the most direct corridor.
        """
        origin_zone   = self.zone_manager.get_zone_for_station(origin_station) or "NR"
        dest_zone     = self.zone_manager.get_zone_for_station(destination_station) or "SR"

        # Simplified corridor logic: find intermediate zones
        intermediate = self._find_intermediate_zones(origin_zone, dest_zone)
        boundary_stations = self._get_boundary_handoff_stations(
            origin_zone, dest_zone, intermediate
        )

        if estimated_distance_km <= 0:
            estimated_distance_km = random.uniform(400, 2800)

        avg_speed_kmh = {"RAJDHANI": 90, "VANDE": 120, "EXPRESS": 75,
                         "FREIGHT": 45, "NORMAL": 60}.get(train_type, 70)
        duration_hours = estimated_distance_km / avg_speed_kmh

        route_id = f"XZRT_{train_id}_{origin_zone}_{dest_zone}"
        route = CrossZonalRoute(
            route_id=route_id,
            train_id=train_id,
            origin_station=origin_station,
            destination_station=destination_station,
            origin_zone=origin_zone,
            destination_zone=dest_zone,
            intermediate_zones=intermediate,
            boundary_handoff_stations=boundary_stations,
            estimated_duration_hours=round(duration_hours, 2),
            estimated_distance_km=round(estimated_distance_km, 1),
            priority=train_type,
        )
        self._active_routes[route_id] = route
        self._train_routes[train_id] = route_id

        # Register train in its origin zone
        self.zone_manager.register_train_in_zone(train_id, origin_zone)
        logger.info("Planned cross-zonal route %s: %s → %s via %s",
                    route_id, origin_zone, dest_zone, intermediate)
        return route

    def _find_intermediate_zones(self, origin: str, destination: str) -> List[str]:
        """Very lightweight corridor heuristic based on Indian rail geography."""
        # Pre-defined major corridors (simplified)
        corridors: Dict[Tuple[str, str], List[str]] = {
            ("NR", "SR"):  ["NCR", "WCR", "CR", "SCR"],
            ("NR", "ER"):  ["NCR", "ECR"],
            ("WR", "ER"):  ["CR", "SCR", "SER"],
            ("NR", "WR"):  ["NCR", "WCR"],
            ("ER", "SR"):  ["SER", "SCR", "SR"],
            ("NWR", "SR"): ["WR", "CR", "SCR"],
            ("NR", "SCR"): ["NCR", "WCR", "CR"],
            ("NFR", "NR"): ["ER", "ECR"],
        }
        key = (origin, destination)
        rev_key = (destination, origin)
        if key in corridors:
            return corridors[key]
        if rev_key in corridors:
            return list(reversed(corridors[rev_key]))
        # Generic fallback: no intermediates (adjacent zones)
        return []

    def _get_boundary_handoff_stations(
        self,
        origin_zone: str,
        dest_zone: str,
        intermediate_zones: List[str],
    ) -> List[str]:
        """Collect the boundary stations at each zonal handoff point."""
        stations = []
        all_zones = [origin_zone] + intermediate_zones + [dest_zone]
        boundary_map = self.zone_manager._boundary_to_zone
        # For each pair of consecutive zones, pick a shared boundary station
        for i in range(len(all_zones) - 1):
            from_z = all_zones[i]
            to_z   = all_zones[i + 1]
            zone_obj = self.zone_manager.zones.get(to_z)
            if zone_obj and zone_obj.boundary_stations:
                stations.append(next(iter(zone_obj.boundary_stations)))
        return stations

    # ------------------------------------------------------------------
    # Inter-Zonal Handoff Processing
    # ------------------------------------------------------------------

    def process_handoff(
        self,
        train_id: str,
        at_station: str,
        delay_minutes: float = 0.0,
        passenger_km: float = 0.0,
        energy_kwh: float = 0.0,
    ) -> Optional[Dict]:
        """
        Trigger an inter-zonal handoff for a train at a boundary station.

        Auto-determines source and target zones from the route plan.
        """
        route_id = self._train_routes.get(train_id)
        if not route_id:
            logger.warning("No route registered for train %s; handoff skipped.", train_id)
            return None

        route = self._active_routes[route_id]
        current_zone = self.zone_manager._train_to_zone.get(train_id, route.origin_zone)

        # Determine next zone in the route sequence
        all_zones = route.all_zones()
        try:
            idx = all_zones.index(current_zone)
            next_zone = all_zones[idx + 1]
        except (ValueError, IndexError):
            logger.info("Train %s has reached final zone %s.", train_id, current_zone)
            return None

        return self.zone_manager.process_zonal_handoff(
            train_id=train_id,
            from_zone=current_zone,
            to_zone=next_zone,
            at_station=at_station,
            delay_minutes=delay_minutes,
            passenger_km=passenger_km,
            energy_kwh=energy_kwh,
        )

    # ------------------------------------------------------------------
    # National Alert System
    # ------------------------------------------------------------------

    def raise_alert(
        self,
        alert_type: str,
        zone_code: str,
        description: str,
        severity: str = "HIGH",
        station_id: Optional[str] = None,
        affected_train_ids: Optional[List[str]] = None,
    ) -> NationalAlert:
        self._alert_counter += 1
        alert_id = f"NALRT_{self._alert_counter:05d}"
        alert = NationalAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            zone_code=zone_code,
            station_id=station_id,
            description=description,
            affected_train_ids=affected_train_ids or [],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._alerts[alert_id] = alert
        logger.warning("NATIONAL ALERT [%s] %s – %s: %s",
                       severity, alert_id, zone_code, description)
        # Propagate to zone incident counter
        if zone_code in self.zone_manager.zones:
            self.zone_manager.zones[zone_code].record_incident()
        return alert

    def resolve_alert(self, alert_id: str) -> bool:
        alert = self._alerts.get(alert_id)
        if not alert:
            return False
        alert.resolved = True
        logger.info("Alert %s resolved.", alert_id)
        return True

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        alerts = [a for a in self._alerts.values() if not a.resolved]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return [a.to_dict() for a in sorted(alerts, key=lambda x: x.created_at, reverse=True)]

    # ------------------------------------------------------------------
    # Fleet Utilisation
    # ------------------------------------------------------------------

    def get_fleet_utilisation(self) -> List[Dict]:
        return [r.to_dict() for r in self._fleet_data.values()]

    def update_fleet_record(
        self,
        fleet_type: str,
        in_service_delta: int = 0,
        maintenance_delta: int = 0,
    ) -> None:
        rec = self._fleet_data.get(fleet_type)
        if not rec:
            return
        rec.units_in_service = max(0, rec.units_in_service + in_service_delta)
        rec.units_under_maintenance = max(0, rec.units_under_maintenance + maintenance_delta)
        settled = rec.units_in_service + rec.units_under_maintenance + rec.units_reserved
        if settled > 0:
            rec.utilisation_pct = rec.units_in_service / settled * 100.0

    # ------------------------------------------------------------------
    # Dashboard Data
    # ------------------------------------------------------------------

    def get_ncr_dashboard(self) -> Dict:
        """
        Return a complete National Control Room dashboard payload.
        Suitable for direct consumption by the NCR frontend widget.
        """
        national_kpi = self.zone_manager.get_national_kpi()
        active_alerts = self.get_active_alerts()
        fleet = self.get_fleet_utilisation()
        alert_zones = self.zone_manager.get_alert_zones(punctuality_threshold=80.0)

        return {
            "ncr_dashboard": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "national_kpi": national_kpi,
            "active_alerts": active_alerts,
            "alert_count": len(active_alerts),
            "alert_zones": alert_zones,
            "fleet_utilisation": fleet,
            "active_cross_zonal_routes": len(self._active_routes),
            "handoff_log_recent": self.zone_manager.get_handoff_log(limit=20),
        }

    def get_route_status(self, train_id: str) -> Optional[Dict]:
        route_id = self._train_routes.get(train_id)
        if not route_id:
            return None
        route = self._active_routes[route_id]
        current_zone = self.zone_manager._train_to_zone.get(train_id, route.origin_zone)
        return {
            "train_id": train_id,
            "route_id": route_id,
            "current_zone": current_zone,
            "origin_zone": route.origin_zone,
            "destination_zone": route.destination_zone,
            "intermediate_zones": route.intermediate_zones,
            "priority": route.priority,
            "distance_km": route.estimated_distance_km,
            "duration_hours": route.estimated_duration_hours,
        }


# Module-level singleton
national_coordinator = NationalCoordinator()
