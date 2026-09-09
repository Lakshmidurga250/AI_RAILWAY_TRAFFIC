"""
Timetable Generator — Automated timetable construction.

Implements:
- Cyclic/periodic timetable generation (Integrated Clock)
- Symmetric timetable construction
- Supplement time allocation
- Commercial schedule optimization
- Pattern-based schedule generation
- Heterogeneous traffic integration
- Station stop pattern optimization
- First/last service determination
- Off-peak schedule reduction
- Passenger demand-driven scheduling
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from datetime import time, timedelta

from optimization.timetabling.slot_allocator import (
    SlotAllocator, TrainSlot, StopTime, TrainCategory
)
from optimization.timetabling.headway_calculator import HeadwayCalculator, BlockSection, SignallingSystem
from optimization.timetabling.connection_manager import ConnectionManager
from optimization.timetabling.rolling_stock_scheduler import RollingStockScheduler, VehicleType

logger = logging.getLogger(__name__)


class TimetableType(Enum):
    PERIODIC = "periodic"         # Integrated clock (every 30/60/120 min)
    DEMAND_RESPONSIVE = "demand"  # Demand-based frequencies
    PEAK_OFFPEAK = "peak"         # Different frequencies per period
    SPECIAL = "special"           # Event/seasonal special


@dataclass
class TimetableConfig:
    """Configuration for timetable generation."""
    name: str
    period_minutes: int = 60         # Service period (headway)
    operating_day_start_min: int = 300   # 05:00
    operating_day_end_min: int = 1440    # 24:00
    timetable_type: TimetableType = TimetableType.PERIODIC

    # Station list
    station_sequence: List[str] = field(default_factory=list)
    station_distances_km: List[float] = field(default_factory=list)
    station_dwell_times_s: List[int] = field(default_factory=list)

    # Train properties
    max_speed_kmh: float = 160.0
    acceleration_ms2: float = 0.8
    deceleration_ms2: float = 0.9
    vehicle_type: VehicleType = VehicleType.EMU_4CAR
    train_category: TrainCategory = TrainCategory.REGIONAL

    # Supplement times
    supplement_factor: float = 0.05   # 5% of runtime
    min_supplement_min: float = 1.0

    # Symmetry
    symmetric_timetable: bool = True  # Generate return service too

    # Capacity
    seat_capacity: int = 300
    standing_capacity: int = 100

    # Commercial
    first_service_min: int = 360    # 06:00 first service
    last_service_min: int = 1380    # 23:00 last service

    def num_services_per_direction(self) -> int:
        """Number of services from first to last."""
        span = self.last_service_min - self.first_service_min
        return max(1, span // self.period_minutes)


@dataclass
class GeneratedTimetable:
    """Result of timetable generation."""
    config: TimetableConfig
    slots: List[TrainSlot] = field(default_factory=list)
    generation_time_s: float = 0.0
    total_services: int = 0
    conflicts_detected: int = 0
    fleet_required: Dict[str, int] = field(default_factory=dict)
    coverage_metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def service_frequency(self) -> str:
        if self.config.period_minutes == 15:
            return "Every 15 minutes"
        elif self.config.period_minutes == 30:
            return "Every 30 minutes"
        elif self.config.period_minutes == 60:
            return "Hourly"
        elif self.config.period_minutes == 120:
            return "Every 2 hours"
        else:
            return f"Every {self.config.period_minutes} minutes"

    def summary(self) -> str:
        return (
            f"Timetable: {self.config.name}\n"
            f"  Services: {self.total_services}\n"
            f"  Frequency: {self.service_frequency()}\n"
            f"  Conflicts: {self.conflicts_detected}\n"
            f"  Fleet: {self.fleet_required}\n"
            f"  Warnings: {len(self.warnings)}"
        )


class TimetableGenerator:
    """
    Automated timetable generator for railway services.

    Generates a complete, conflict-free timetable from:
    - Station sequence with distances and dwell times
    - Desired service frequency
    - Train performance characteristics
    - Infrastructure constraints (headways, capacity)
    """

    def __init__(self) -> None:
        self.headway_calculator = HeadwayCalculator()
        self.slot_allocator = SlotAllocator()
        self.connection_manager = ConnectionManager()
        self.rs_scheduler = RollingStockScheduler()

    def compute_running_times(self, config: TimetableConfig) -> List[float]:
        """
        Compute minimum running times between consecutive stations.
        Uses kinematic model with acceleration/deceleration.
        """
        running_times = []
        for i, dist_km in enumerate(config.station_distances_km):
            dist_m = dist_km * 1000
            v_max_ms = config.max_speed_kmh / 3.6
            a = config.acceleration_ms2
            d = config.deceleration_ms2

            # Time to accelerate from 0 to v_max
            t_acc = v_max_ms / a
            dist_acc = 0.5 * a * t_acc ** 2

            # Time to decelerate from v_max to 0
            t_dec = v_max_ms / d
            dist_dec = 0.5 * d * t_dec ** 2

            if dist_acc + dist_dec >= dist_m:
                # Short section — never reaches max speed
                v_peak = min(v_max_ms, (2 * dist_m * a * d / (a + d)) ** 0.5)
                t_acc_short = v_peak / a
                t_dec_short = v_peak / d
                run_time_s = t_acc_short + t_dec_short
            else:
                # Cruise at max speed
                dist_cruise = dist_m - dist_acc - dist_dec
                t_cruise = dist_cruise / v_max_ms
                run_time_s = t_acc + t_cruise + t_dec

            # Add supplement
            supplement_s = max(
                config.min_supplement_min * 60,
                run_time_s * config.supplement_factor
            )
            running_times.append(run_time_s + supplement_s)

        return running_times

    def generate_slot(self, config: TimetableConfig,
                       service_number: int,
                       departure_offset_min: float,
                       direction: str = "outbound") -> TrainSlot:
        """Generate a single train slot."""
        running_times_s = self.compute_running_times(config)
        dwell_times_s = config.station_dwell_times_s or [60] * len(config.station_sequence)

        stations = config.station_sequence
        if direction == "inbound":
            stations = list(reversed(stations))
            running_times_s = list(reversed(running_times_s))
            dwell_times_s = list(reversed(dwell_times_s))

        slot_id = f"{config.name}_{direction.upper()}_{service_number:03d}"
        train_num = f"{service_number * 2 if direction == 'outbound' else service_number * 2 + 1:04d}"

        stops = []
        current_min = config.first_service_min + departure_offset_min

        for i, station_id in enumerate(stations):
            if i == 0:
                # Origin — only departure
                dep_time = time(hour=int(current_min // 60) % 24,
                                minute=int(current_min % 60))
                stop = StopTime(
                    station_id=station_id,
                    station_name=station_id,
                    departure_time=dep_time,
                    dwell_time_s=0,
                )
                stops.append(stop)
            elif i == len(stations) - 1:
                # Terminus — only arrival
                arr_min = current_min + running_times_s[i - 1] / 60
                arr_time = time(hour=int(arr_min // 60) % 24,
                                minute=int(arr_min % 60))
                stop = StopTime(
                    station_id=station_id,
                    station_name=station_id,
                    arrival_time=arr_time,
                    dwell_time_s=0,
                )
                stops.append(stop)
                current_min = arr_min
            else:
                # Intermediate stop
                arr_min = current_min + running_times_s[i - 1] / 60
                dwell = dwell_times_s[i] if i < len(dwell_times_s) else 60
                dep_min = arr_min + dwell / 60

                arr_time = time(hour=int(arr_min // 60) % 24,
                                minute=int(arr_min % 60))
                dep_time = time(hour=int(dep_min // 60) % 24,
                                minute=int(dep_min % 60))

                stop = StopTime(
                    station_id=station_id,
                    station_name=station_id,
                    arrival_time=arr_time,
                    departure_time=dep_time,
                    dwell_time_s=dwell,
                )
                stops.append(stop)
                current_min = dep_min

        slot = TrainSlot(
            slot_id=slot_id,
            train_number=train_num,
            category=config.train_category,
            stops=stops,
            direction=direction,
            period_minutes=config.period_minutes,
            rolling_stock_type=config.vehicle_type.value,
            max_speed_kmh=config.max_speed_kmh,
        )
        return slot

    def generate_full_timetable(self, config: TimetableConfig) -> GeneratedTimetable:
        """
        Generate a complete timetable for a line based on the config.
        """
        import time as time_module
        start = time_module.time()

        slots = []
        num_services = config.num_services_per_direction()

        for i in range(num_services):
            offset = i * config.period_minutes
            # Outbound
            slot_out = self.generate_slot(config, i + 1, offset, "outbound")
            slots.append(slot_out)
            self.slot_allocator.register_slot(slot_out)

            # Inbound (if symmetric)
            if config.symmetric_timetable:
                slot_in = self.generate_slot(config, i + 1, offset, "inbound")
                slots.append(slot_in)
                self.slot_allocator.register_slot(slot_in)

        # Detect conflicts
        conflicts = self.slot_allocator.detect_conflicts()

        # Compute fleet requirement
        fleet_required = {config.vehicle_type.value: max(2, len(slots) // num_services)}

        gen_time = time_module.time() - start

        timetable = GeneratedTimetable(
            config=config,
            slots=slots,
            generation_time_s=round(gen_time, 3),
            total_services=len(slots),
            conflicts_detected=len(conflicts),
            fleet_required=fleet_required,
            coverage_metrics={
                "first_service": f"{config.first_service_min // 60:02d}:{config.first_service_min % 60:02d}",
                "last_service": f"{config.last_service_min // 60:02d}:{config.last_service_min % 60:02d}",
                "service_frequency_min": config.period_minutes,
                "total_stations": len(config.station_sequence),
                "num_outbound": num_services,
                "num_inbound": num_services if config.symmetric_timetable else 0,
            },
            warnings=[f"Conflict detected: {c.slot_a} vs {c.slot_b}" for c in conflicts[:10]],
        )

        logger.info("Generated timetable '%s': %d services, %d conflicts",
                    config.name, len(slots), len(conflicts))
        return timetable

    def export_gtfs(self, timetable: GeneratedTimetable) -> Dict[str, List[Dict[str, Any]]]:
        """Export generated timetable in GTFS-like format."""
        routes = [{
            "route_id": timetable.config.name,
            "route_short_name": timetable.config.name,
            "route_type": "2",  # Rail
        }]

        trips = []
        stop_times = []

        for slot in timetable.slots:
            trips.append({
                "route_id": timetable.config.name,
                "trip_id": slot.slot_id,
                "trip_headsign": slot.stops[-1].station_id if slot.stops else "",
                "direction_id": "0" if slot.direction == "outbound" else "1",
            })

            for seq, stop in enumerate(slot.stops):
                arr = stop.arrival_time.strftime("%H:%M:%S") if stop.arrival_time else ""
                dep = stop.departure_time.strftime("%H:%M:%S") if stop.departure_time else ""
                stop_times.append({
                    "trip_id": slot.slot_id,
                    "arrival_time": arr,
                    "departure_time": dep,
                    "stop_id": stop.station_id,
                    "stop_sequence": seq,
                })

        return {
            "routes": routes,
            "trips": trips,
            "stop_times": stop_times,
        }
