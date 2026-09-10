"""
Railway Zone Manager for National-Scale Operations.

Models Indian Railways' 18 zonal railway organisations.  Each zone owns a set
of divisions, stations, tracks and a live train roster.  The ZoneManager
aggregates real-time KPIs (punctuality, throughput, energy, delay) and emits
inter-zonal handoff events when a train crosses a zonal boundary.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Indian Railway Zones (as of 2024)
# ---------------------------------------------------------------------------

class IndianRailwayZone(str, Enum):
    CENTRAL          = "CR"
    EAST_CENTRAL     = "ECR"
    EAST_COAST       = "ECoR"
    EASTERN          = "ER"
    NORTH_CENTRAL    = "NCR"
    NORTH_EASTERN    = "NER"
    NORTH_WESTERN    = "NWR"
    NORTHEAST_FRONTIER = "NFR"
    NORTHERN         = "NR"
    SOUTH_CENTRAL    = "SCR"
    SOUTH_EASTERN    = "SER"
    SOUTH_EAST_CENTRAL = "SECR"
    SOUTH_WESTERN    = "SWR"
    SOUTHERN         = "SR"
    WEST_CENTRAL     = "WCR"
    WESTERN          = "WR"
    METRO_RAILWAY    = "MR"
    KONKAN           = "KR"


@dataclass
class ZonalKPISnapshot:
    """Point-in-time KPI snapshot for a single zone."""
    zone_code: str
    timestamp: datetime
    total_trains_running: int = 0
    trains_on_time: int = 0
    trains_delayed: int = 0
    trains_cancelled: int = 0
    punctuality_pct: float = 0.0
    avg_delay_minutes: float = 0.0
    passenger_km_today: float = 0.0
    freight_tonne_km_today: float = 0.0
    energy_kwh_consumed: float = 0.0
    incidents_today: int = 0
    cross_boundary_handoffs: int = 0

    def to_dict(self) -> Dict:
        return {
            "zone": self.zone_code,
            "timestamp": self.timestamp.isoformat(),
            "trains_running": self.total_trains_running,
            "on_time": self.trains_on_time,
            "delayed": self.trains_delayed,
            "cancelled": self.trains_cancelled,
            "punctuality_pct": round(self.punctuality_pct, 2),
            "avg_delay_min": round(self.avg_delay_minutes, 1),
            "passenger_km": round(self.passenger_km_today, 0),
            "freight_tonne_km": round(self.freight_tonne_km_today, 0),
            "energy_kwh": round(self.energy_kwh_consumed, 1),
            "incidents": self.incidents_today,
            "handoffs": self.cross_boundary_handoffs,
        }


@dataclass
class RailwayZone:
    """A single railway zone with its operational state."""

    zone_code: str
    full_name: str
    headquarters: str
    divisions: List[str] = field(default_factory=list)
    boundary_stations: Set[str] = field(default_factory=set)  # handoff points

    # Live operational state
    active_train_ids: Set[str] = field(default_factory=set)
    station_ids: Set[str] = field(default_factory=set)
    track_ids: Set[str] = field(default_factory=set)

    # Cumulative day counters
    _trains_on_time: int = field(default=0, repr=False)
    _trains_delayed: int = field(default=0, repr=False)
    _trains_cancelled: int = field(default=0, repr=False)
    _total_delay_min: float = field(default=0.0, repr=False)
    _passenger_km: float = field(default=0.0, repr=False)
    _freight_tonne_km: float = field(default=0.0, repr=False)
    _energy_kwh: float = field(default=0.0, repr=False)
    _incidents: int = field(default=0, repr=False)
    _handoffs: int = field(default=0, repr=False)

    def record_train_arrival(
        self,
        train_id: str,
        delay_minutes: float,
        passenger_km: float = 0.0,
        freight_tonne_km: float = 0.0,
        energy_kwh: float = 0.0,
    ) -> None:
        """Register the arrival of a train into this zone's statistics."""
        if delay_minutes <= 5.0:
            self._trains_on_time += 1
        else:
            self._trains_delayed += 1
            self._total_delay_min += delay_minutes
        self._passenger_km += passenger_km
        self._freight_tonne_km += freight_tonne_km
        self._energy_kwh += energy_kwh

    def record_cancellation(self) -> None:
        self._trains_cancelled += 1

    def record_incident(self) -> None:
        self._incidents += 1

    def record_handoff(self) -> None:
        self._handoffs += 1

    def get_kpi_snapshot(self) -> ZonalKPISnapshot:
        total = self._trains_on_time + self._trains_delayed
        punctuality = (self._trains_on_time / total * 100.0) if total > 0 else 100.0
        avg_delay = (self._total_delay_min / self._trains_delayed) if self._trains_delayed > 0 else 0.0
        return ZonalKPISnapshot(
            zone_code=self.zone_code,
            timestamp=datetime.now(timezone.utc),
            total_trains_running=len(self.active_train_ids),
            trains_on_time=self._trains_on_time,
            trains_delayed=self._trains_delayed,
            trains_cancelled=self._trains_cancelled,
            punctuality_pct=punctuality,
            avg_delay_minutes=avg_delay,
            passenger_km_today=self._passenger_km,
            freight_tonne_km_today=self._freight_tonne_km,
            energy_kwh_consumed=self._energy_kwh,
            incidents_today=self._incidents,
            cross_boundary_handoffs=self._handoffs,
        )

    def reset_daily_counters(self) -> None:
        self._trains_on_time = 0
        self._trains_delayed = 0
        self._trains_cancelled = 0
        self._total_delay_min = 0.0
        self._passenger_km = 0.0
        self._freight_tonne_km = 0.0
        self._energy_kwh = 0.0
        self._incidents = 0
        self._handoffs = 0


class ZoneManager:
    """
    Manages the lifecycle and KPI aggregation of all Indian Railway zones.

    Responsibilities:
    - Zone registry with boundary station mapping.
    - Train entry / exit across zonal boundaries (inter-zonal handoff).
    - Real-time KPI snapshots per zone and national aggregate.
    - Operational alerts for under-performing zones.
    """

    # Seed data: Indian Railway zones with HQ and sample boundary stations.
    ZONE_SEED: List[Tuple[str, str, str, List[str]]] = [
        ("CR",  "Central Railway",              "Mumbai CSMT", ["PUNE", "NGP", "BSL"]),
        ("ECR", "East Central Railway",          "Hajipur",     ["PNBE", "MGS", "DNR"]),
        ("ECoR","East Coast Railway",            "Bhubaneswar", ["BBS", "VSKP", "SBP"]),
        ("ER",  "Eastern Railway",               "Kolkata",     ["HWH", "KOAA", "BHW"]),
        ("NCR", "North Central Railway",         "Prayagraj",   ["ALD", "AGC", "JHS"]),
        ("NER", "North Eastern Railway",         "Gorakhpur",   ["GKP", "LJN", "BSB"]),
        ("NWR", "North Western Railway",         "Jaipur",      ["JP", "ADI", "AII"]),
        ("NFR", "Northeast Frontier Railway",    "Maligaon",    ["GHY", "DBRG", "NCB"]),
        ("NR",  "Northern Railway",              "New Delhi",   ["NDLS", "DLI", "UMB"]),
        ("SCR", "South Central Railway",         "Secunderabad",["SC", "HYB", "TPTY"]),
        ("SER", "South Eastern Railway",         "Garden Reach",["KGP", "CKP", "ADRA"]),
        ("SECR","South East Central Railway",    "Bilaspur",    ["BSP", "R", "NGP"]),
        ("SWR", "South Western Railway",         "Hubballi",    ["UBL", "YPR", "MYS"]),
        ("SR",  "Southern Railway",              "Chennai",     ["MAS", "CBE", "TVC"]),
        ("WCR", "West Central Railway",          "Jabalpur",    ["JBP", "BPL", "KOTA"]),
        ("WR",  "Western Railway",               "Mumbai Church",["BCT", "RTM", "BRC"]),
        ("MR",  "Metro Railway",                 "Kolkata",     ["DUMDUM", "ESPLANADE"]),
        ("KR",  "Konkan Railway",                "Navi Mumbai", ["RN", "MAO", "KUDAL"]),
    ]

    def __init__(self) -> None:
        self.zones: Dict[str, RailwayZone] = {}
        self._boundary_to_zone: Dict[str, str] = {}   # station_id -> zone_code
        self._train_to_zone: Dict[str, str] = {}       # train_id -> current zone_code
        self._handoff_log: List[Dict] = []
        self._initialize_zones()

    def _initialize_zones(self) -> None:
        for row in self.ZONE_SEED:
            code, name, hq, boundary_stations = row
            zone = RailwayZone(
                zone_code=code,
                full_name=name,
                headquarters=hq,
                boundary_stations=set(boundary_stations),
            )
            self.zones[code] = zone
            for stn in boundary_stations:
                self._boundary_to_zone[stn] = code
        logger.info("ZoneManager initialised with %d zones.", len(self.zones))

    def get_zone_for_station(self, station_id: str) -> Optional[str]:
        """Look up which zone a station belongs to (boundary check first)."""
        return self._boundary_to_zone.get(station_id)

    def register_train_in_zone(self, train_id: str, zone_code: str) -> None:
        """Place a train into a zone when it starts service."""
        if zone_code in self.zones:
            self.zones[zone_code].active_train_ids.add(train_id)
            self._train_to_zone[train_id] = zone_code

    def process_zonal_handoff(
        self,
        train_id: str,
        from_zone: str,
        to_zone: str,
        at_station: str,
        delay_minutes: float = 0.0,
        passenger_km: float = 0.0,
        energy_kwh: float = 0.0,
    ) -> Dict:
        """
        Transfer a train from one zone to another at a boundary station.

        Records arrival KPIs in the source zone, updates the train's zone
        assignment, and emits a structured handoff event.
        """
        if from_zone not in self.zones or to_zone not in self.zones:
            logger.warning("Handoff ignored: unknown zone(s) %s -> %s", from_zone, to_zone)
            return {}

        # Exit source zone
        src = self.zones[from_zone]
        src.active_train_ids.discard(train_id)
        src.record_train_arrival(train_id, delay_minutes, passenger_km, 0.0, energy_kwh)
        src.record_handoff()

        # Enter destination zone
        dst = self.zones[to_zone]
        dst.active_train_ids.add(train_id)
        self._train_to_zone[train_id] = to_zone

        event = {
            "event": "ZONAL_HANDOFF",
            "train_id": train_id,
            "from_zone": from_zone,
            "to_zone": to_zone,
            "at_station": at_station,
            "delay_minutes": round(delay_minutes, 1),
            "passenger_km_segment": round(passenger_km, 1),
            "energy_kwh_segment": round(energy_kwh, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._handoff_log.append(event)
        logger.info("Handoff: train %s from %s to %s at %s", train_id, from_zone, to_zone, at_station)
        return event

    def get_zone_kpi(self, zone_code: str) -> Optional[Dict]:
        zone = self.zones.get(zone_code)
        if zone is None:
            return None
        return zone.get_kpi_snapshot().to_dict()

    def get_national_kpi(self) -> Dict:
        """Aggregate KPIs across all zones for a national summary dashboard."""
        snapshots = [z.get_kpi_snapshot() for z in self.zones.values()]
        total_trains   = sum(s.total_trains_running for s in snapshots)
        total_on_time  = sum(s.trains_on_time for s in snapshots)
        total_delayed  = sum(s.trains_delayed for s in snapshots)
        total_cancelled = sum(s.trains_cancelled for s in snapshots)
        total_pax_km   = sum(s.passenger_km_today for s in snapshots)
        total_freight  = sum(s.freight_tonne_km_today for s in snapshots)
        total_energy   = sum(s.energy_kwh_consumed for s in snapshots)
        total_incidents = sum(s.incidents_today for s in snapshots)
        total_handoffs  = sum(s.cross_boundary_handoffs for s in snapshots)

        settled = total_on_time + total_delayed
        nat_punctuality = (total_on_time / settled * 100.0) if settled > 0 else 100.0

        return {
            "national_kpi": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "zones_active": len(self.zones),
            "trains_running": total_trains,
            "trains_on_time": total_on_time,
            "trains_delayed": total_delayed,
            "trains_cancelled": total_cancelled,
            "national_punctuality_pct": round(nat_punctuality, 2),
            "passenger_km_today": round(total_pax_km, 0),
            "freight_tonne_km_today": round(total_freight, 0),
            "energy_kwh_consumed": round(total_energy, 1),
            "incidents_today": total_incidents,
            "zonal_handoffs_today": total_handoffs,
            "zones": [s.to_dict() for s in snapshots],
        }

    def get_handoff_log(self, limit: int = 50) -> List[Dict]:
        return self._handoff_log[-limit:]

    def reset_daily_metrics(self) -> None:
        """Call at midnight to reset all day-cumulative counters."""
        for zone in self.zones.values():
            zone.reset_daily_counters()
        self._handoff_log.clear()
        logger.info("Daily zonal metrics reset.")

    def get_alert_zones(self, punctuality_threshold: float = 80.0) -> List[Dict]:
        """Return zones whose punctuality has dropped below threshold."""
        alerts = []
        for code, zone in self.zones.items():
            snap = zone.get_kpi_snapshot()
            if snap.trains_on_time + snap.trains_delayed > 0:
                if snap.punctuality_pct < punctuality_threshold:
                    alerts.append({
                        "zone": code,
                        "full_name": zone.full_name,
                        "punctuality_pct": snap.punctuality_pct,
                        "avg_delay_min": snap.avg_delay_minutes,
                        "severity": "CRITICAL" if snap.punctuality_pct < 60 else "WARNING",
                    })
        return sorted(alerts, key=lambda x: x["punctuality_pct"])
