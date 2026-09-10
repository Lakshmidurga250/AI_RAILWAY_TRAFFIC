"""
Passenger Flow Simulator and Demand Forecaster.

Models real-time and forecast passenger demand across Indian Railways
station network. Covers:

  - Station-level boarding/alighting counts with temporal patterns
  - Interchange passenger flows (connecting train demand)
  - Crowd density heat-mapping per platform and concourse zone
  - Demand surge detection (festivals, events, school seasons)
  - Overcrowding alerts and capacity threshold management
  - Seat occupancy and standing load factor computation
  - Season-adjusted demand curves (peak/off-peak, day-of-week, holiday)
  - Fare-demand elasticity modelling
  - Real-time headcount via gate count simulation
  - Evacuation capacity planning (emergency throughput)
"""

from __future__ import annotations

import logging
import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class StationCategory(str, Enum):
    A1   = "A1"    # Highest footfall (Mumbai, Delhi, Chennai, Kolkata central)
    A    = "A"     # Major junction
    B    = "B"     # District headquarters
    C    = "C"     # Smaller town
    D    = "D"     # Rural halt
    E    = "E"     # Flag station


class PlatformZone(str, Enum):
    CONCOURSE   = "CONCOURSE"
    PLATFORM    = "PLATFORM"
    WAITING     = "WAITING"
    TICKET_HALL = "TICKET_HALL"
    ENTRANCE    = "ENTRANCE"
    EXIT        = "EXIT"
    OVERBRIDGE  = "FOB"
    UNDERPASS   = "SUB"


class DemandSurgeType(str, Enum):
    NORMAL       = "NORMAL"
    FESTIVAL     = "FESTIVAL"    # Diwali, Holi, Eid, Pongal …
    EXAM_SEASON  = "EXAM_SEASON" # UPSC, Board exams, JEE
    SPORTS_EVENT = "SPORTS_EVENT"
    POLITICAL    = "POLITICAL"
    EMERGENCY    = "EMERGENCY"
    WEATHER      = "WEATHER"     # flood/cyclone evacuation


class TrainClass(str, Enum):
    AC_FIRST      = "1A"
    AC_TWO_TIER   = "2A"
    AC_THREE_TIER = "3A"
    SLEEPER       = "SL"
    GENERAL       = "GEN"
    SECOND_SITTING = "2S"
    AC_CHAIR_CAR  = "CC"
    EXEC_CHAIR    = "EC"
    VANDE_CHAIR   = "VC"


class OccupancyStatus(str, Enum):
    EMPTY         = "EMPTY"           # < 20%
    LOW           = "LOW"             # 20-50%
    MODERATE      = "MODERATE"        # 50-75%
    HIGH          = "HIGH"            # 75-90%
    FULL          = "FULL"            # 90-100%
    OVERCROWDED   = "OVERCROWDED"     # > 100%
    CRITICAL      = "CRITICAL"        # > 150%


# ─────────────────────────────────────────────────────────────────────────────
# Capacity constants per class
# ─────────────────────────────────────────────────────────────────────────────

CLASS_CAPACITY: Dict[str, int] = {
    "1A":  24,
    "2A":  46,
    "3A":  64,
    "SL":  72,
    "GEN": 90,   # seated; standing ~120 extra
    "2S":  108,
    "CC":  78,
    "EC":  56,
    "VC":  96,
}

STANDING_ALLOWANCE: Dict[str, int] = {
    "GEN": 120,
    "SL":  20,
    "2S":  30,
    "CC":  0,
    "1A":  0,
    "2A":  0,
    "3A":  0,
    "EC":  0,
    "VC":  0,
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PassengerCount:
    """Snapshot of passenger counts at a station at a point in time."""
    station_id:        str
    timestamp:         datetime
    total_present:     int = 0
    boarding:          int = 0
    alighting:         int = 0
    transiting:        int = 0
    gate_in:           int = 0
    gate_out:          int = 0
    waiting_area:      int = 0
    platform_counts:   Dict[str, int] = field(default_factory=dict)   # platform_id -> count
    zone_counts:       Dict[str, int] = field(default_factory=dict)   # PlatformZone -> count
    surge_type:        DemandSurgeType = DemandSurgeType.NORMAL
    surge_multiplier:  float = 1.0

    def occupancy_pct(self, station_capacity: int) -> float:
        if station_capacity <= 0:
            return 0.0
        return self.total_present / station_capacity * 100.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id":       self.station_id,
            "timestamp":        self.timestamp.isoformat(),
            "total_present":    self.total_present,
            "boarding":         self.boarding,
            "alighting":        self.alighting,
            "transiting":       self.transiting,
            "gate_in":          self.gate_in,
            "gate_out":         self.gate_out,
            "waiting_area":     self.waiting_area,
            "platform_counts":  self.platform_counts,
            "zone_counts":      self.zone_counts,
            "surge_type":       self.surge_type.value,
            "surge_multiplier": round(self.surge_multiplier, 2),
        }


@dataclass
class CoachOccupancy:
    """Passenger occupancy for a single coach on a train."""
    coach_id:      str
    coach_number:  str
    train_class:   TrainClass
    capacity:      int
    reserved_seats: int
    boarded:       int = 0
    alighted:      int = 0

    @property
    def current_pax(self) -> int:
        return self.boarded - self.alighted

    @property
    def occupancy_pct(self) -> float:
        if self.capacity <= 0:
            return 0.0
        return self.current_pax / self.capacity * 100.0

    @property
    def load_factor(self) -> float:
        standing = STANDING_ALLOWANCE.get(self.train_class.value, 0)
        total_capacity = self.capacity + standing
        return self.current_pax / max(1, total_capacity)

    @property
    def status(self) -> OccupancyStatus:
        pct = self.occupancy_pct
        if pct < 20:   return OccupancyStatus.EMPTY
        if pct < 50:   return OccupancyStatus.LOW
        if pct < 75:   return OccupancyStatus.MODERATE
        if pct < 90:   return OccupancyStatus.HIGH
        if pct < 100:  return OccupancyStatus.FULL
        if pct < 150:  return OccupancyStatus.OVERCROWDED
        return OccupancyStatus.CRITICAL

    def board(self, count: int) -> int:
        """Board passengers; returns actual boarded (may be less than requested)."""
        standing = STANDING_ALLOWANCE.get(self.train_class.value, 0)
        max_load = self.capacity + standing
        actual = min(count, max(0, max_load - self.current_pax))
        self.boarded += actual
        return actual

    def alight(self, count: int) -> int:
        actual = min(count, self.current_pax)
        self.alighted += actual
        return actual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coach_id":      self.coach_id,
            "coach_number":  self.coach_number,
            "class":         self.train_class.value,
            "capacity":      self.capacity,
            "current_pax":   self.current_pax,
            "occupancy_pct": round(self.occupancy_pct, 1),
            "load_factor":   round(self.load_factor, 3),
            "status":        self.status.value,
        }


@dataclass
class TrainLoadProfile:
    """Full passenger load profile for a train across all coaches."""
    train_id:   str
    train_no:   str
    route_id:   str
    coaches:    List[CoachOccupancy] = field(default_factory=list)
    timestamp:  datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_pax(self) -> int:
        return sum(c.current_pax for c in self.coaches)

    @property
    def total_capacity(self) -> int:
        return sum(c.capacity for c in self.coaches)

    @property
    def overall_occupancy_pct(self) -> float:
        if self.total_capacity <= 0:
            return 0.0
        return self.total_pax / self.total_capacity * 100.0

    @property
    def overall_status(self) -> OccupancyStatus:
        pct = self.overall_occupancy_pct
        if pct < 20:   return OccupancyStatus.EMPTY
        if pct < 50:   return OccupancyStatus.LOW
        if pct < 75:   return OccupancyStatus.MODERATE
        if pct < 90:   return OccupancyStatus.HIGH
        if pct < 100:  return OccupancyStatus.FULL
        if pct < 150:  return OccupancyStatus.OVERCROWDED
        return OccupancyStatus.CRITICAL

    def board_at_station(self, station_id: str, pax_by_class: Dict[str, int]) -> Dict[str, int]:
        """Board passengers at a station. Returns dict of class -> actual boarded."""
        actual: Dict[str, int] = {}
        for cls_val, count in pax_by_class.items():
            try:
                tc = TrainClass(cls_val)
            except ValueError:
                continue
            for coach in self.coaches:
                if coach.train_class == tc and count > 0:
                    boarded = coach.board(count)
                    actual[cls_val] = actual.get(cls_val, 0) + boarded
                    count -= boarded
        return actual

    def alight_at_station(self, station_id: str, pax_by_class: Dict[str, int]) -> Dict[str, int]:
        actual: Dict[str, int] = {}
        for cls_val, count in pax_by_class.items():
            try:
                tc = TrainClass(cls_val)
            except ValueError:
                continue
            for coach in self.coaches:
                if coach.train_class == tc and count > 0:
                    alighted = coach.alight(count)
                    actual[cls_val] = actual.get(cls_val, 0) + alighted
                    count -= alighted
        return actual

    def to_dict(self) -> Dict[str, Any]:
        return {
            "train_id":            self.train_id,
            "train_no":            self.train_no,
            "total_pax":           self.total_pax,
            "total_capacity":      self.total_capacity,
            "occupancy_pct":       round(self.overall_occupancy_pct, 1),
            "status":              self.overall_status.value,
            "timestamp":           self.timestamp.isoformat(),
            "coaches":             [c.to_dict() for c in self.coaches],
        }


@dataclass
class DemandForecastPoint:
    """A single demand forecast point for a station at a specific hour."""
    station_id:     str
    forecast_date:  date
    hour:           int    # 0-23
    predicted_pax:  int
    confidence_pct: float  # 0-100
    surge_type:     DemandSurgeType
    model_version:  str = "v1.0"
    upper_bound:    int = 0
    lower_bound:    int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id":     self.station_id,
            "date":           self.forecast_date.isoformat(),
            "hour":           self.hour,
            "predicted_pax":  self.predicted_pax,
            "lower_bound":    self.lower_bound,
            "upper_bound":    self.upper_bound,
            "confidence_pct": round(self.confidence_pct, 1),
            "surge_type":     self.surge_type.value,
            "model_version":  self.model_version,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Temporal demand curves
# ─────────────────────────────────────────────────────────────────────────────

# Normalised hourly demand factors (24h, index = hour) – relative to daily mean
HOURLY_DEMAND_PROFILE = [
    0.15, 0.10, 0.08, 0.07, 0.12, 0.30,   # 00-05
    0.75, 1.40, 1.80, 1.50, 1.20, 1.10,   # 06-11
    1.00, 1.05, 1.10, 1.20, 1.45, 1.70,   # 12-17
    1.80, 1.60, 1.30, 1.00, 0.65, 0.35,   # 18-23
]

DAY_OF_WEEK_FACTOR = {
    0: 1.00,   # Monday
    1: 0.95,
    2: 0.92,
    3: 0.95,
    4: 1.10,   # Friday surge
    5: 1.25,   # Saturday
    6: 0.85,   # Sunday (fewer commuters)
}

FESTIVAL_SURGE_MULTIPLIER = {
    DemandSurgeType.FESTIVAL:     2.8,
    DemandSurgeType.EXAM_SEASON:  1.6,
    DemandSurgeType.SPORTS_EVENT: 1.8,
    DemandSurgeType.POLITICAL:    1.4,
    DemandSurgeType.EMERGENCY:    3.5,
    DemandSurgeType.WEATHER:      2.2,
    DemandSurgeType.NORMAL:       1.0,
}

# Average daily footfall by category (passengers/day)
CATEGORY_BASE_FOOTFALL = {
    StationCategory.A1: 500_000,
    StationCategory.A:  150_000,
    StationCategory.B:   50_000,
    StationCategory.C:   15_000,
    StationCategory.D:    3_000,
    StationCategory.E:      500,
}


# ─────────────────────────────────────────────────────────────────────────────
# Demand Forecaster
# ─────────────────────────────────────────────────────────────────────────────

class PassengerDemandForecaster:
    """
    Generates hourly passenger demand forecasts for a station.

    Uses:
    - Category base footfall
    - Hourly temporal pattern
    - Day-of-week adjustment
    - Surge multiplier (festival, event, emergency)
    - Random noise for realism
    """

    def __init__(self, noise_std_pct: float = 8.0) -> None:
        self.noise_std_pct = noise_std_pct

    def forecast_day(
        self,
        station_id: str,
        category: StationCategory,
        for_date: date,
        surge_type: DemandSurgeType = DemandSurgeType.NORMAL,
        custom_multiplier: float = 1.0,
    ) -> List[DemandForecastPoint]:
        base          = CATEGORY_BASE_FOOTFALL[category]
        day_factor    = DAY_OF_WEEK_FACTOR.get(for_date.weekday(), 1.0)
        surge_factor  = FESTIVAL_SURGE_MULTIPLIER.get(surge_type, 1.0) * custom_multiplier
        daily_total   = base * day_factor * surge_factor

        points: List[DemandForecastPoint] = []
        for hour in range(24):
            hour_factor   = HOURLY_DEMAND_PROFILE[hour]
            raw           = daily_total * hour_factor / sum(HOURLY_DEMAND_PROFILE)
            noise         = random.gauss(0, raw * self.noise_std_pct / 100.0)
            predicted     = max(0, int(raw + noise))
            ci_half       = int(raw * 0.12)           # ±12% CI
            confidence    = 95.0 if surge_type == DemandSurgeType.NORMAL else 80.0
            points.append(DemandForecastPoint(
                station_id    = station_id,
                forecast_date = for_date,
                hour          = hour,
                predicted_pax = predicted,
                lower_bound   = max(0, predicted - ci_half),
                upper_bound   = predicted + ci_half,
                confidence_pct= confidence,
                surge_type    = surge_type,
            ))
        return points

    def forecast_range(
        self,
        station_id: str,
        category: StationCategory,
        start_date: date,
        days: int = 7,
        surge_type: DemandSurgeType = DemandSurgeType.NORMAL,
    ) -> Dict[str, List[DemandForecastPoint]]:
        result: Dict[str, List[DemandForecastPoint]] = {}
        for i in range(days):
            d = start_date + timedelta(days=i)
            result[d.isoformat()] = self.forecast_day(station_id, category, d, surge_type)
        return result

    def peak_hours(self, points: List[DemandForecastPoint], top_n: int = 3) -> List[DemandForecastPoint]:
        return sorted(points, key=lambda p: p.predicted_pax, reverse=True)[:top_n]

    def daily_total(self, points: List[DemandForecastPoint]) -> int:
        return sum(p.predicted_pax for p in points)

    def generate_od_matrix(
        self,
        station_ids: List[str],
        categories: Dict[str, StationCategory],
        for_date: date,
    ) -> Dict[Tuple[str, str], int]:
        """
        Generate an origin-destination demand matrix for a list of stations.
        Demand from O to D is proportional to the product of their base footfalls,
        with a distance-decay exponent applied.
        """
        od: Dict[Tuple[str, str], int] = {}
        for origin in station_ids:
            cat_o = categories.get(origin, StationCategory.C)
            base_o = CATEGORY_BASE_FOOTFALL[cat_o]
            for dest in station_ids:
                if origin == dest:
                    continue
                cat_d = categories.get(dest, StationCategory.C)
                base_d = CATEGORY_BASE_FOOTFALL[cat_d]
                # Gravity model
                day_idx = for_date.weekday()
                flow = int(math.sqrt(base_o * base_d) * DAY_OF_WEEK_FACTOR.get(day_idx, 1.0) * 0.002)
                flow = max(0, flow + random.randint(-flow // 10, flow // 10))
                od[(origin, dest)] = flow
        return od


# ─────────────────────────────────────────────────────────────────────────────
# Crowd Density Manager
# ─────────────────────────────────────────────────────────────────────────────

class CrowdDensityManager:
    """
    Real-time crowd density management and overcrowding alert system.

    Tracks passenger counts per zone at each station and raises alerts
    when density exceeds safe thresholds.
    """

    DENSITY_THRESHOLDS = {
        PlatformZone.CONCOURSE:   4.0,    # persons / m²
        PlatformZone.PLATFORM:    3.5,
        PlatformZone.WAITING:     3.0,
        PlatformZone.TICKET_HALL: 2.5,
        PlatformZone.ENTRANCE:    4.0,
        PlatformZone.EXIT:        4.0,
        PlatformZone.OVERBRIDGE:  2.0,
        PlatformZone.UNDERPASS:   2.0,
    }

    # Zone areas by station category (m²)
    ZONE_AREAS = {
        StationCategory.A1: {
            PlatformZone.CONCOURSE:   10_000,
            PlatformZone.PLATFORM:     8_000,
            PlatformZone.WAITING:      4_000,
            PlatformZone.TICKET_HALL:  2_000,
            PlatformZone.ENTRANCE:     1_500,
            PlatformZone.EXIT:         1_500,
            PlatformZone.OVERBRIDGE:   1_200,
            PlatformZone.UNDERPASS:    1_000,
        },
        StationCategory.A: {
            PlatformZone.CONCOURSE:    3_000,
            PlatformZone.PLATFORM:     2_500,
            PlatformZone.WAITING:      1_200,
            PlatformZone.TICKET_HALL:    600,
            PlatformZone.ENTRANCE:       400,
            PlatformZone.EXIT:           400,
            PlatformZone.OVERBRIDGE:     350,
            PlatformZone.UNDERPASS:      300,
        },
        StationCategory.B: {
            PlatformZone.CONCOURSE:    1_000,
            PlatformZone.PLATFORM:       900,
            PlatformZone.WAITING:        400,
            PlatformZone.TICKET_HALL:    200,
            PlatformZone.ENTRANCE:       150,
            PlatformZone.EXIT:           150,
            PlatformZone.OVERBRIDGE:     120,
            PlatformZone.UNDERPASS:      100,
        },
    }

    def __init__(self) -> None:
        # station_id -> {zone -> current_count}
        self._counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._station_categories: Dict[str, StationCategory] = {}
        self._alerts: List[Dict[str, Any]] = []

    def register_station(self, station_id: str, category: StationCategory) -> None:
        self._station_categories[station_id] = category
        # Initialise all zones to 0
        for zone in PlatformZone:
            self._counts[station_id][zone.value] = 0

    def update_zone_count(self, station_id: str, zone: PlatformZone, count: int) -> List[Dict[str, Any]]:
        """Update headcount for a zone and return any new alerts."""
        self._counts[station_id][zone.value] = max(0, count)
        return self._check_density_alerts(station_id, zone)

    def add_to_zone(self, station_id: str, zone: PlatformZone, delta: int) -> List[Dict[str, Any]]:
        current = self._counts[station_id][zone.value]
        return self.update_zone_count(station_id, zone, current + delta)

    def _get_zone_area(self, station_id: str, zone: PlatformZone) -> float:
        cat = self._station_categories.get(station_id, StationCategory.B)
        areas = self.ZONE_AREAS.get(cat, self.ZONE_AREAS[StationCategory.B])
        return float(areas.get(zone, 500))

    def _check_density_alerts(self, station_id: str, zone: PlatformZone) -> List[Dict[str, Any]]:
        count     = self._counts[station_id][zone.value]
        area      = self._get_zone_area(station_id, zone)
        density   = count / max(area, 1.0)
        threshold = self.DENSITY_THRESHOLDS.get(zone, 3.0)
        new_alerts: List[Dict[str, Any]] = []

        if density >= threshold * 1.3:
            alert = {
                "type":       "CROWD_CRITICAL",
                "station_id": station_id,
                "zone":       zone.value,
                "density":    round(density, 2),
                "threshold":  threshold,
                "count":      count,
                "severity":   "CRITICAL",
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "action":     f"Immediate crowd control at {zone.value}; consider closing entry gates",
            }
            self._alerts.append(alert)
            new_alerts.append(alert)
            logger.critical("CROWD CRITICAL: %s zone %s density %.1f/m²", station_id, zone.value, density)
        elif density >= threshold:
            alert = {
                "type":       "CROWD_WARNING",
                "station_id": station_id,
                "zone":       zone.value,
                "density":    round(density, 2),
                "threshold":  threshold,
                "count":      count,
                "severity":   "WARNING",
                "timestamp":  datetime.now(timezone.utc).isoformat(),
                "action":     f"Deploy additional staff to {zone.value}",
            }
            self._alerts.append(alert)
            new_alerts.append(alert)

        return new_alerts

    def get_station_density_snapshot(self, station_id: str) -> Dict[str, Any]:
        counts = self._counts.get(station_id, {})
        zones_info = []
        for zone in PlatformZone:
            count  = counts.get(zone.value, 0)
            area   = self._get_zone_area(station_id, zone)
            density = count / max(area, 1.0)
            thresh = self.DENSITY_THRESHOLDS.get(zone, 3.0)
            zones_info.append({
                "zone":       zone.value,
                "count":      count,
                "area_m2":    area,
                "density":    round(density, 2),
                "threshold":  thresh,
                "pct_of_max": round(density / thresh * 100, 1),
                "status":     "CRITICAL" if density >= thresh * 1.3 else ("WARNING" if density >= thresh else "OK"),
            })
        return {
            "station_id": station_id,
            "category":   self._station_categories.get(station_id, StationCategory.B).value,
            "zones":      zones_info,
            "total_pax":  sum(counts.values()),
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        }

    def get_active_alerts(self, station_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if station_id:
            return [a for a in self._alerts if a["station_id"] == station_id]
        return self._alerts[-100:]

    def evacuation_capacity(self, station_id: str) -> Dict[str, Any]:
        """Estimate evacuation throughput rate for a station."""
        cat  = self._station_categories.get(station_id, StationCategory.B)
        area_map = self.ZONE_AREAS.get(cat, self.ZONE_AREAS[StationCategory.B])
        exit_area = (
            area_map.get(PlatformZone.EXIT, 150) +
            area_map.get(PlatformZone.OVERBRIDGE, 120) +
            area_map.get(PlatformZone.UNDERPASS, 100)
        )
        # 1 person/m²/second through exit channels
        throughput_per_minute = int(exit_area * 0.7 * 60)
        total_pax = sum(self._counts.get(station_id, {}).values())
        minutes_to_evacuate = total_pax / max(throughput_per_minute, 1)
        return {
            "station_id":            station_id,
            "total_pax":             total_pax,
            "exit_area_m2":          exit_area,
            "throughput_per_minute": throughput_per_minute,
            "estimated_evac_minutes": round(minutes_to_evacuate, 1),
            "safe_within_15_min":    minutes_to_evacuate <= 15,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Passenger Flow Simulator
# ─────────────────────────────────────────────────────────────────────────────

class PassengerFlowSimulator:
    """
    Full passenger flow simulation across a multi-station network.

    Combines demand forecasting, real-time crowd density management,
    and train load profiling into a unified operational view.
    """

    def __init__(self) -> None:
        self.forecaster     = PassengerDemandForecaster()
        self.crowd_manager  = CrowdDensityManager()
        self._station_cats: Dict[str, StationCategory] = {}
        self._station_caps: Dict[str, int]             = {}
        self._train_loads:  Dict[str, TrainLoadProfile] = {}
        self._counts:       Dict[str, PassengerCount]   = {}

    def register_station(
        self,
        station_id: str,
        category: StationCategory,
        capacity: int,
    ) -> None:
        self._station_cats[station_id] = category
        self._station_caps[station_id] = capacity
        self.crowd_manager.register_station(station_id, category)
        logger.debug("Station registered: %s (%s) cap=%d", station_id, category.value, capacity)

    def register_train(self, profile: TrainLoadProfile) -> None:
        self._train_loads[profile.train_id] = profile

    # ── Real-time updates ────────────────────────────────────────────────

    def record_gate_entry(self, station_id: str, count: int) -> PassengerCount:
        pc = self._get_or_create_count(station_id)
        pc.gate_in      += count
        pc.total_present += count
        pc.waiting_area  += count
        self.crowd_manager.add_to_zone(station_id, PlatformZone.TICKET_HALL, count)
        return pc

    def record_gate_exit(self, station_id: str, count: int) -> PassengerCount:
        pc = self._get_or_create_count(station_id)
        pc.gate_out      += count
        pc.total_present  = max(0, pc.total_present - count)
        return pc

    def record_boarding(self, station_id: str, train_id: str, count: int,
                        coach_class: str = "SL") -> Dict[str, Any]:
        pc = self._get_or_create_count(station_id)
        pc.boarding      += count
        pc.total_present  = max(0, pc.total_present - count)
        self.crowd_manager.add_to_zone(station_id, PlatformZone.PLATFORM, -count)

        result: Dict[str, Any] = {"boarded": count, "refused": 0}
        if train_id in self._train_loads:
            actual = self._train_loads[train_id].board_at_station(
                station_id, {coach_class: count}
            )
            result["boarded_by_class"] = actual
        return result

    def record_alighting(self, station_id: str, train_id: str, count: int,
                         coach_class: str = "SL") -> Dict[str, Any]:
        pc = self._get_or_create_count(station_id)
        pc.alighting     += count
        pc.total_present += count
        self.crowd_manager.add_to_zone(station_id, PlatformZone.PLATFORM, count)

        result: Dict[str, Any] = {"alighted": count}
        if train_id in self._train_loads:
            actual = self._train_loads[train_id].alight_at_station(
                station_id, {coach_class: count}
            )
            result["alighted_by_class"] = actual
        return result

    def _get_or_create_count(self, station_id: str) -> PassengerCount:
        if station_id not in self._counts:
            self._counts[station_id] = PassengerCount(
                station_id = station_id,
                timestamp  = datetime.now(timezone.utc),
            )
        return self._counts[station_id]

    # ── Forecasting ──────────────────────────────────────────────────────

    def get_forecast(
        self,
        station_id: str,
        for_date: Optional[date] = None,
        surge_type: DemandSurgeType = DemandSurgeType.NORMAL,
    ) -> List[Dict[str, Any]]:
        cat    = self._station_cats.get(station_id, StationCategory.B)
        target = for_date or date.today()
        points = self.forecaster.forecast_day(station_id, cat, target, surge_type)
        return [p.to_dict() for p in points]

    def get_od_matrix(
        self, for_date: Optional[date] = None
    ) -> Dict[str, int]:
        stations = list(self._station_cats.keys())
        od = self.forecaster.generate_od_matrix(stations, self._station_cats, for_date or date.today())
        return {f"{o}→{d}": v for (o, d), v in od.items()}

    # ── Dashboard payload ────────────────────────────────────────────────

    def get_network_flow_dashboard(self) -> Dict[str, Any]:
        station_summaries = []
        for sid in self._station_cats:
            pc    = self._counts.get(sid)
            snap  = self.crowd_manager.get_station_density_snapshot(sid)
            cap   = self._station_caps.get(sid, 0)
            total = pc.total_present if pc else 0
            station_summaries.append({
                "station_id":    sid,
                "category":      self._station_cats[sid].value,
                "total_present": total,
                "capacity":      cap,
                "occupancy_pct": round(total / max(cap, 1) * 100, 1),
                "zones":         snap["zones"],
                "alerts":        len(self.crowd_manager.get_active_alerts(sid)),
            })

        train_summaries = [
            {k: v for k, v in load.to_dict().items() if k != "coaches"}
            for load in self._train_loads.values()
        ]

        return {
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "stations_tracked": len(station_summaries),
            "trains_tracked":   len(train_summaries),
            "stations":         station_summaries,
            "trains":           train_summaries,
            "total_active_pax": sum(s["total_present"] for s in station_summaries),
            "network_alerts":   self.crowd_manager.get_active_alerts(),
        }

    def get_train_load_report(self, train_id: str) -> Optional[Dict[str, Any]]:
        load = self._train_loads.get(train_id)
        if not load:
            return None
        return load.to_dict()

    def get_station_report(self, station_id: str) -> Dict[str, Any]:
        pc   = self._counts.get(station_id, PassengerCount(station_id=station_id, timestamp=datetime.now(timezone.utc)))
        snap = self.crowd_manager.get_station_density_snapshot(station_id)
        evac = self.crowd_manager.evacuation_capacity(station_id)
        return {
            "station_id":       station_id,
            "live_count":       pc.to_dict(),
            "density_snapshot": snap,
            "evacuation":       evac,
            "alerts":           self.crowd_manager.get_active_alerts(station_id),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_sample_simulator() -> PassengerFlowSimulator:
    """Build a PassengerFlowSimulator pre-populated with major Indian Railway stations."""
    sim = PassengerFlowSimulator()
    stations = [
        ("NDLS", StationCategory.A1, 80_000),
        ("BCT",  StationCategory.A1, 70_000),
        ("HWH",  StationCategory.A1, 60_000),
        ("MAS",  StationCategory.A1, 55_000),
        ("SC",   StationCategory.A,  30_000),
        ("PUNE", StationCategory.A,  25_000),
        ("JP",   StationCategory.A,  20_000),
        ("LJN",  StationCategory.B,  10_000),
        ("GKP",  StationCategory.B,   8_000),
        ("BSP",  StationCategory.B,   6_000),
    ]
    for sid, cat, cap in stations:
        sim.register_station(sid, cat, cap)

    # Seed some live counts
    for sid, cat, cap in stations:
        daily_base = CATEGORY_BASE_FOOTFALL[cat]
        hour = datetime.now(timezone.utc).hour
        factor = HOURLY_DEMAND_PROFILE[hour]
        current = int(daily_base * factor / sum(HOURLY_DEMAND_PROFILE) * random.uniform(0.8, 1.2))
        sim.record_gate_entry(sid, current)

        # Distribute across zones
        for zone in PlatformZone:
            zone_share = random.uniform(0.05, 0.25)
            sim.crowd_manager.update_zone_count(sid, zone, int(current * zone_share))

    return sim


# Module-level singleton
passenger_flow_sim = build_sample_simulator()
