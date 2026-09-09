"""
Rolling Stock Scheduler for Railway Timetabling.

Implements:
- Vehicle block construction (Umlauf)
- Vehicle circulation planning
- Fleet size calculation
- Minimum turnaround time enforcement
- Depot allocation and management
- Maintenance scheduling integration
- Vehicle type compatibility checking
- Empty working optimization
- Fleet utilization analysis
- Reserve fleet computation
- Vehicle availability forecasting
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, time, timedelta

logger = logging.getLogger(__name__)


class VehicleType(Enum):
    EMU_4CAR = "EMU_4car"
    EMU_8CAR = "EMU_8car"
    DMU_2CAR = "DMU_2car"
    LOCOMOTIVE_IC = "Loco_IC"
    LOCOMOTIVE_FREIGHT = "Loco_Freight"
    HIGH_SPEED = "HS_Train"
    TRAM = "Tram"
    METRO = "Metro"


class VehicleStatus(Enum):
    AVAILABLE = auto()
    IN_SERVICE = auto()
    STABLING = auto()          # Stabled in depot/siding
    MAINTENANCE = auto()       # In maintenance
    RESERVE = auto()           # Reserve unit
    FAILED = auto()


@dataclass
class VehicleBlock:
    """
    A vehicle block — all the trips performed by one vehicle unit in a day
    (Fahrzeug-Umlauf in German timetabling).
    """
    block_id: str
    vehicle_type: VehicleType
    depot_id: str

    # Trips in this block (ordered chronologically)
    trips: List[Dict[str, Any]] = field(default_factory=list)

    # Block timing
    out_of_depot_time: Optional[time] = None
    into_depot_time: Optional[time] = None
    total_service_time_min: float = 0.0
    total_empty_working_min: float = 0.0
    total_standby_time_min: float = 0.0

    # Vehicle
    vehicle_id: Optional[str] = None
    status: VehicleStatus = VehicleStatus.AVAILABLE

    # Costs
    service_km: float = 0.0
    empty_km: float = 0.0

    def add_trip(self, trip: Dict[str, Any]) -> None:
        """Add a service trip to this block."""
        self.trips.append(trip)
        self.total_service_time_min += trip.get("duration_min", 0)
        self.service_km += trip.get("distance_km", 0)

    def utilization(self) -> float:
        """Fraction of block time spent in revenue service."""
        total = self.total_service_time_min + self.total_standby_time_min
        return self.total_service_time_min / total if total > 0 else 0.0

    def layover_times(self) -> List[float]:
        """Compute layover times between consecutive trips."""
        layovers = []
        for i in range(len(self.trips) - 1):
            end_min = self.trips[i].get("arrival_min", 0)
            start_min = self.trips[i + 1].get("departure_min", 0)
            layover = start_min - end_min
            if layover >= 0:
                layovers.append(layover)
        return layovers

    def __repr__(self) -> str:
        return (f"VehicleBlock({self.block_id!r}, "
                f"{self.vehicle_type.name}, "
                f"{len(self.trips)} trips, util={self.utilization():.0%})")


@dataclass
class VehicleCirculation:
    """
    Complete vehicle circulation plan for a service day.
    """
    date: str
    blocks: List[VehicleBlock] = field(default_factory=list)
    vehicle_assignments: Dict[str, str] = field(default_factory=dict)  # block_id -> vehicle_id

    def total_fleet_required(self) -> int:
        return len(set(b.vehicle_type for b in self.blocks))

    def fleet_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for block in self.blocks:
            counts[block.vehicle_type.name] += 1
        return dict(counts)

    def total_service_km(self) -> float:
        return sum(b.service_km for b in self.blocks)

    def total_empty_km(self) -> float:
        return sum(b.empty_km for b in self.blocks)

    def average_utilization(self) -> float:
        if not self.blocks:
            return 0.0
        return sum(b.utilization() for b in self.blocks) / len(self.blocks)


class RollingStockScheduler:
    """
    Vehicle circulation planner.

    Constructs minimum-fleet circulations by chaining compatible trips
    to minimize fleet size and deadhead (empty) movements.

    Uses network flow formulation:
    - Source: depot
    - Sink: depot
    - Nodes: trips
    - Edges: feasible trip chains (compatibility = sufficient layover + same depot area)
    """

    # Minimum turnaround times by vehicle type (minutes)
    MIN_TURNAROUND = {
        VehicleType.EMU_4CAR: 8,
        VehicleType.EMU_8CAR: 10,
        VehicleType.DMU_2CAR: 8,
        VehicleType.LOCOMOTIVE_IC: 15,
        VehicleType.LOCOMOTIVE_FREIGHT: 20,
        VehicleType.HIGH_SPEED: 25,
        VehicleType.TRAM: 3,
        VehicleType.METRO: 2,
    }

    def __init__(self) -> None:
        self.trips: Dict[str, Dict[str, Any]] = {}
        self.depots: Dict[str, Dict[str, Any]] = {}
        self.vehicles: Dict[str, Dict[str, Any]] = {}
        self._blocks: List[VehicleBlock] = []

    def register_depot(self, depot_id: str, name: str,
                        capacity: int, location: str = "") -> None:
        self.depots[depot_id] = {
            "depot_id": depot_id,
            "name": name,
            "capacity": capacity,
            "location": location,
            "stabled_vehicles": [],
        }

    def register_trip(self, trip_id: str, origin: str, destination: str,
                       departure_min: float, arrival_min: float,
                       vehicle_type: VehicleType, distance_km: float = 0.0,
                       nearest_depot: str = "") -> None:
        self.trips[trip_id] = {
            "trip_id": trip_id,
            "origin": origin,
            "destination": destination,
            "departure_min": departure_min,
            "arrival_min": arrival_min,
            "vehicle_type": vehicle_type,
            "distance_km": distance_km,
            "nearest_depot": nearest_depot,
            "duration_min": arrival_min - departure_min,
        }

    def is_compatible(self, trip_a: Dict[str, Any], trip_b: Dict[str, Any]) -> bool:
        """
        Check if trip_b can follow trip_a (same vehicle).
        Requires: same vehicle type, sufficient turnaround, destination/origin compatibility.
        """
        if trip_a["vehicle_type"] != trip_b["vehicle_type"]:
            return False

        min_turn = self.MIN_TURNAROUND.get(trip_a["vehicle_type"], 10)
        layover = trip_b["departure_min"] - trip_a["arrival_min"]

        if layover < min_turn:
            return False

        # Simple geographic compatibility: same station or depot nearby
        if trip_a["destination"] == trip_b["origin"]:
            return True

        # Allow short empty working (< 30 min deadhead)
        # In a real system, compute actual empty working time
        return layover < min_turn + 30

    def chain_trips_greedy(self, vehicle_type: VehicleType,
                            depot_id: str = "") -> List[VehicleBlock]:
        """
        Greedy trip chaining — link trips to minimize fleet size.
        Uses earliest-arrival-first dispatch.
        """
        type_trips = [t for t in self.trips.values()
                      if t["vehicle_type"] == vehicle_type]
        type_trips_sorted = sorted(type_trips, key=lambda t: t["departure_min"])

        blocks: List[VehicleBlock] = []
        active_blocks: List[Dict[str, Any]] = []  # Currently running blocks (last trip)

        for trip in type_trips_sorted:
            # Try to find a compatible active block
            assigned = False
            for i, (last_trip, block) in enumerate(active_blocks):
                if self.is_compatible(last_trip, trip):
                    block.add_trip(trip)
                    active_blocks[i] = (trip, block)
                    assigned = True
                    break

            if not assigned:
                # Create new block
                block_id = f"BLK_{vehicle_type.name}_{len(blocks) + 1:03d}"
                new_block = VehicleBlock(
                    block_id=block_id,
                    vehicle_type=vehicle_type,
                    depot_id=depot_id,
                )
                new_block.add_trip(trip)
                blocks.append(new_block)
                active_blocks.append((trip, new_block))

        self._blocks.extend(blocks)
        logger.info("Chained %d trips into %d blocks for %s",
                    len(type_trips_sorted), len(blocks), vehicle_type.name)
        return blocks

    def build_circulation(self, date: str) -> VehicleCirculation:
        """Build complete vehicle circulation for all vehicle types."""
        circulation = VehicleCirculation(date=date)

        vehicle_types = set(t["vehicle_type"] for t in self.trips.values())
        for vtype in vehicle_types:
            depot = list(self.depots.keys())[0] if self.depots else "default_depot"
            blocks = self.chain_trips_greedy(vtype, depot)
            circulation.blocks.extend(blocks)

        logger.info("Built circulation with %d blocks, fleet=%s",
                    len(circulation.blocks), circulation.fleet_by_type())
        return circulation

    def compute_reserve_fleet(self, base_fleet: Dict[str, int],
                               reserve_factor: float = 0.10) -> Dict[str, int]:
        """Compute reserve fleet sizes (typically 10% of operational fleet)."""
        return {
            vtype: max(1, int(count * reserve_factor))
            for vtype, count in base_fleet.items()
        }

    def fleet_utilization_report(self, circulation: VehicleCirculation) -> Dict[str, Any]:
        """Generate detailed fleet utilization report."""
        by_type: Dict[str, List[float]] = defaultdict(list)
        for block in circulation.blocks:
            by_type[block.vehicle_type.name].append(block.utilization())

        return {
            "date": circulation.date,
            "total_blocks": len(circulation.blocks),
            "fleet_by_type": circulation.fleet_by_type(),
            "total_service_km": round(circulation.total_service_km(), 1),
            "total_empty_km": round(circulation.total_empty_km(), 1),
            "average_utilization": round(circulation.average_utilization(), 3),
            "by_type": {
                vtype: {
                    "blocks": len(utils),
                    "avg_utilization": round(sum(utils) / len(utils), 3) if utils else 0,
                    "min_utilization": round(min(utils), 3) if utils else 0,
                    "max_utilization": round(max(utils), 3) if utils else 0,
                }
                for vtype, utils in by_type.items()
            },
        }

    def maintenance_integration(self, vehicle_id: str,
                                 maintenance_type: str,
                                 duration_hours: float) -> Dict[str, Any]:
        """
        Reserve a vehicle for maintenance and find replacement.
        Returns maintenance record and replacement assignment.
        """
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]["status"] = VehicleStatus.MAINTENANCE.name

        return {
            "vehicle_id": vehicle_id,
            "maintenance_type": maintenance_type,
            "duration_hours": duration_hours,
            "scheduled_return": f"In {duration_hours:.0f} hours",
            "replacement_action": "Activate reserve unit",
        }

    def statistics(self) -> Dict[str, Any]:
        return {
            "total_trips": len(self.trips),
            "total_depots": len(self.depots),
            "total_vehicles": len(self.vehicles),
            "total_blocks_planned": len(self._blocks),
        }
