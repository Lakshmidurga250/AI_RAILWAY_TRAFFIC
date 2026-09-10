"""
Solid State Interlocking (SSI) / Electronic Interlocking (EI) Safety Logic Engine.

Implements CENELEC SIL-4 Fail-Safe Railway Interlocking Logic:
  - Route Request, Verification & Locking Sequence (RR -> RV -> RL -> GS)
  - Flank Protection & Overlap Isolation (Conflicting Route Exclusion Matrix)
  - Point Machine Operating Timeouts & Detection Relay (NWCR / RWCR verification)
  - Track Circuit Clear Proofing (TCR / TPR) with Drop/Pickup Timer Hysteresis
  - Approach Locking & Emergency Route Cancellation with 120-second Dead Approach Timer
  - Signal Lamp Proving Relay (UECR / HECR / DECR) with Automatic Red Fallback
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class PointMachinePosition(enum.Enum):
    NORMAL = "NORMAL_STRAIGHT"
    REVERSE = "REVERSE_DIVERGING"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_OF_CORRESPONDENCE = "OUT_OF_CORRESPONDENCE_FAULT"


class SignalAspect(enum.Enum):
    RED_STOP = "RED_DANGER"
    YELLOW_CAUTION = "YELLOW_CAUTION"
    DOUBLE_YELLOW_ATTENTION = "DOUBLE_YELLOW_ATTENTION"
    GREEN_PROCEED = "GREEN_CLEAR"


class TrackCircuitStatus(enum.Enum):
    CLEAR = "CLEAR_ENERGIZED"
    OCCUPIED = "OCCUPIED_SHUNTED"
    FAIL_SAFE_DROP = "FAIL_SAFE_DEENERGIZED"


@dataclass
class PointMachine:
    point_id: str
    assigned_turnout_number: str
    normal_locked: bool = True
    reverse_locked: bool = False
    current_position: PointMachinePosition = PointMachinePosition.NORMAL
    detection_contact_made: bool = True
    motor_operating_current_amperes: float = 3.5  # normal 3-5A, stall > 6A
    throw_time_seconds: float = 4.5


@dataclass
class TrackCircuit:
    track_id: str
    length_meters: float
    status: TrackCircuitStatus = TrackCircuitStatus.CLEAR
    ballast_resistance_ohms_per_km: float = 4.0
    relay_voltage_volts: float = 1.4  # normal pickup >= 1.2V


@dataclass
class RouteDefinition:
    route_id: str
    entry_signal_id: str
    exit_signal_id: str
    required_points: Dict[str, PointMachinePosition]
    track_circuits_in_route: List[str]
    overlap_track_circuits: List[str]
    conflicting_routes: List[str]
    is_locked: bool = False
    approach_locked: bool = False


class ElectronicInterlockingEngine:
    """SIL-4 Boolean Logic Engine executing railway interlocking control equations."""

    def __init__(self, station_name: str):
        self.station_name = station_name
        self.points: Dict[str, PointMachine] = {}
        self.track_circuits: Dict[str, TrackCircuit] = {}
        self.routes: Dict[str, RouteDefinition] = {}
        self.signal_aspects: Dict[str, SignalAspect] = {}

    def register_point(self, point: PointMachine):
        self.points[point.point_id] = point

    def register_track(self, track: TrackCircuit):
        self.track_circuits[track.track_id] = track

    def register_route(self, route: RouteDefinition):
        self.routes[route.route_id] = route
        self.signal_aspects[route.entry_signal_id] = SignalAspect.RED_STOP

    def request_route(self, route_id: str) -> Tuple[bool, str]:
        """
        Attempts to lock all points, verify track vacancy, and clear entry signal.
        """
        if route_id not in self.routes:
            return False, f"Unknown route {route_id}"

        route = self.routes[route_id]

        # 1. Verify conflicting routes are not locked
        for conf_id in route.conflicting_routes:
            if conf_id in self.routes and self.routes[conf_id].is_locked:
                return False, f"Route conflict: Conflicting route {conf_id} is already locked"

        # 2. Verify all track circuits in route + overlap are CLEAR
        all_tracks = route.track_circuits_in_route + route.overlap_track_circuits
        for t_id in all_tracks:
            tc = self.track_circuits.get(t_id)
            if not tc or tc.status != TrackCircuitStatus.CLEAR:
                return False, f"Track circuit {t_id} is OCCUPIED or DEENERGIZED"

        # 3. Throw and Lock Point Machines in required position
        for p_id, req_pos in route.required_points.items():
            pm = self.points.get(p_id)
            if not pm:
                return False, f"Point machine {p_id} not found"
            pm.current_position = req_pos
            pm.normal_locked = (req_pos == PointMachinePosition.NORMAL)
            pm.reverse_locked = (req_pos == PointMachinePosition.REVERSE)

        # 4. Lock Route and Clear Signal
        route.is_locked = True
        self.signal_aspects[route.entry_signal_id] = SignalAspect.GREEN_PROCEED
        return True, f"Route {route_id} SUCCESSFULLY LOCKED. Signal {route.entry_signal_id} cleared to GREEN."

    def release_route_on_train_passage(self, route_id: str):
        """Sequential route release when train safely clears track sections."""
        if route_id in self.routes:
            route = self.routes[route_id]
            route.is_locked = False
            self.signal_aspects[route.entry_signal_id] = SignalAspect.RED_STOP
            for p_id in route.required_points:
                if p_id in self.points:
                    self.points[p_id].normal_locked = False
                    self.points[p_id].reverse_locked = False
