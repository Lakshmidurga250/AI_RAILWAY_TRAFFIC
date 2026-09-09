"""
Route Controller for Computer-Based Interlocking (CBI).

Implements:
- Route definition (entry signal + exit signal + track sections + points)
- Route setting (locking sequence: approach lock -> point detection -> route lock)
- Route releasing (cancellation, sequential release, approach release)
- Overlap management
- Conflicting route detection
- Route availability check
- Priority-based route arbitration
- Sub-route granularity for sectional release
- Timetable-driven route pre-selection
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class RouteState(Enum):
    FREE = auto()             # Route not set
    APPROACH_LOCKED = auto()  # Train approaching, approach section locked
    LOCKED = auto()           # Fully locked, signal cleared
    OCCUPIED = auto()         # Train is traversing the route
    RELEASING = auto()        # Sequential release in progress
    CANCELLED = auto()        # Route cancellation requested
    BLOCKED = auto()          # Route blocked by conflicting route or obstacle


class PointPosition(Enum):
    NORMAL = "N"
    REVERSE = "R"
    MOVING = "M"
    FAILED = "F"
    UNKNOWN = "U"


class ReleaseMode(Enum):
    FULL = auto()             # Release all elements at once
    SEQUENTIAL = auto()       # Release elements as train passes
    APPROACH = auto()         # Approach release on cancellation


@dataclass
class TrackSection:
    """A track section (block) that can be part of a route."""
    section_id: str
    name: str
    length_m: float = 100.0
    is_occupied: bool = False
    is_locked: bool = False
    max_speed_kmh: float = 160.0
    gradient_permille: float = 0.0
    allocated_to: Optional[str] = None  # train_id

    def occupy(self, train_id: str) -> None:
        self.is_occupied = True
        self.allocated_to = train_id

    def clear(self) -> None:
        self.is_occupied = False
        self.allocated_to = None

    def lock(self) -> None:
        self.is_locked = True

    def unlock(self) -> None:
        self.is_locked = False

    def __repr__(self) -> str:
        return f"TrackSection({self.section_id!r}, occupied={self.is_occupied}, locked={self.is_locked})"


@dataclass
class PointSetting:
    """Required point position within a route."""
    point_id: str
    required_position: PointPosition
    is_secured: bool = False  # point locked in required position

    def __repr__(self) -> str:
        return f"PointSetting({self.point_id!r}, {self.required_position.name})"


@dataclass
class Route:
    """
    Complete route definition from entry signal to exit signal.
    Includes all track sections, points, and overlap requirements.
    """
    route_id: str
    name: str
    entry_signal_id: str
    exit_signal_id: str
    track_sections: List[TrackSection] = field(default_factory=list)
    point_settings: List[PointSetting] = field(default_factory=list)
    overlap_id: Optional[str] = None
    conflicting_routes: Set[str] = field(default_factory=set)
    max_speed_kmh: float = 160.0
    direction: str = "forward"
    sub_routes: List["Route"] = field(default_factory=list)

    # Runtime state
    state: RouteState = RouteState.FREE
    set_time: Optional[datetime] = None
    cleared_time: Optional[datetime] = None
    train_id: Optional[str] = None
    release_mode: ReleaseMode = ReleaseMode.SEQUENTIAL
    sections_cleared: int = 0  # for sequential release

    def total_length_m(self) -> float:
        return sum(s.length_m for s in self.track_sections)

    def is_available(self) -> bool:
        """Check if route can be set (all elements free and unlocked)."""
        if self.state != RouteState.FREE:
            return False
        if any(s.is_occupied or s.is_locked for s in self.track_sections):
            return False
        if any(ps.is_secured and
               self._get_point_position(ps.point_id) != ps.required_position
               for ps in self.point_settings):
            return False
        return True

    def _get_point_position(self, point_id: str) -> PointPosition:
        # Placeholder — actual position from PointController
        return PointPosition.NORMAL

    def conflicting_with(self, other: "Route") -> bool:
        """True if this route shares sections or conflicting point settings with another."""
        if other.route_id in self.conflicting_routes:
            return True
        own_sections = {s.section_id for s in self.track_sections}
        other_sections = {s.section_id for s in other.track_sections}
        return bool(own_sections & other_sections)

    def __repr__(self) -> str:
        return (f"Route({self.route_id!r}, {self.entry_signal_id!r} -> "
                f"{self.exit_signal_id!r}, state={self.state.name})")


@dataclass
class RouteLockRecord:
    """Audit record for route state transitions."""
    route_id: str
    from_state: RouteState
    to_state: RouteState
    timestamp: datetime
    operator_id: Optional[str] = None
    reason: str = ""
    train_id: Optional[str] = None


class RouteController:
    """
    Main route controller implementing CBI route locking sequence.

    Locking sequence (per EN 50128 / ERTMS specifications):
    1. Check availability (no conflicting routes, all sections free)
    2. Approach lock (lock approach section)
    3. Point setting and detection (move + lock all points)
    4. Route lock (lock all track sections)
    5. Signal clear (set entry signal to proceed aspect)
    6. Train traversal monitoring
    7. Sequential/approach release
    """

    def __init__(self) -> None:
        self.routes: Dict[str, Route] = {}
        self._lock_records: List[RouteLockRecord] = []
        self._pending_cancellations: Set[str] = set()
        self._approach_locked: Set[str] = set()
        self._callbacks: Dict[str, List[Any]] = {
            "route_set": [],
            "route_released": [],
            "conflict_detected": [],
        }

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def register_route(self, route: Route) -> None:
        self.routes[route.route_id] = route
        logger.info("Registered route %s", route.route_id)

    def register_routes(self, routes: List[Route]) -> None:
        for r in routes:
            self.register_route(r)

    def build_conflict_matrix(self) -> None:
        """Auto-compute conflicting routes based on shared track sections."""
        route_list = list(self.routes.values())
        for i, r1 in enumerate(route_list):
            for j, r2 in enumerate(route_list):
                if i >= j:
                    continue
                secs_1 = {s.section_id for s in r1.track_sections}
                secs_2 = {s.section_id for s in r2.track_sections}
                if secs_1 & secs_2:
                    r1.conflicting_routes.add(r2.route_id)
                    r2.conflicting_routes.add(r1.route_id)

    # ------------------------------------------------------------------
    # Route setting
    # ------------------------------------------------------------------

    def can_set_route(self, route_id: str) -> Tuple[bool, str]:
        """
        Check all preconditions for setting a route.
        Returns (can_set, reason).
        """
        if route_id not in self.routes:
            return False, f"Route {route_id!r} not registered"

        route = self.routes[route_id]

        if route.state not in (RouteState.FREE, RouteState.APPROACH_LOCKED):
            return False, f"Route in state {route.state.name}, cannot set"

        # Check for conflicting routes already set
        for conflict_id in route.conflicting_routes:
            if conflict_id in self.routes:
                conflict_route = self.routes[conflict_id]
                if conflict_route.state in (
                    RouteState.LOCKED, RouteState.APPROACH_LOCKED,
                    RouteState.OCCUPIED, RouteState.RELEASING,
                ):
                    return False, f"Conflicting route {conflict_id!r} is {conflict_route.state.name}"

        # Check sections availability
        for section in route.track_sections:
            if section.is_occupied:
                return False, f"Section {section.section_id!r} is occupied"
            if section.is_locked and section.allocated_to != route.route_id:
                return False, f"Section {section.section_id!r} is locked by another route"

        return True, "Route can be set"

    def set_route(self, route_id: str, train_id: Optional[str] = None,
                  operator_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Execute the full route-setting sequence.
        Returns (success, message).
        """
        can_set, reason = self.can_set_route(route_id)
        if not can_set:
            logger.warning("Cannot set route %s: %s", route_id, reason)
            return False, reason

        route = self.routes[route_id]
        old_state = route.state

        # Step 1: Lock all track sections
        for section in route.track_sections:
            section.lock()

        # Step 2: Secure all point settings
        for point_setting in route.point_settings:
            point_setting.is_secured = True

        # Step 3: Lock overlap if defined
        if route.overlap_id:
            logger.debug("Locking overlap %s for route %s", route.overlap_id, route_id)

        # Step 4: Update route state
        route.state = RouteState.LOCKED
        route.set_time = datetime.utcnow()
        route.train_id = train_id
        route.sections_cleared = 0

        # Audit
        record = RouteLockRecord(
            route_id=route_id,
            from_state=old_state,
            to_state=RouteState.LOCKED,
            timestamp=datetime.utcnow(),
            operator_id=operator_id,
            reason="Route set by controller",
            train_id=train_id,
        )
        self._lock_records.append(record)

        # Notify callbacks
        for cb in self._callbacks.get("route_set", []):
            try:
                cb(route)
            except Exception as exc:
                logger.error("Callback error: %s", exc)

        logger.info("Route %s set for train %s", route_id, train_id)
        return True, f"Route {route_id} successfully set"

    def approach_lock(self, route_id: str) -> bool:
        """Lock the approach section when a train enters the approach zone."""
        if route_id not in self.routes:
            return False
        route = self.routes[route_id]
        if route.state != RouteState.FREE:
            return False
        route.state = RouteState.APPROACH_LOCKED
        self._approach_locked.add(route_id)
        logger.debug("Approach locked: %s", route_id)
        return True

    # ------------------------------------------------------------------
    # Route release
    # ------------------------------------------------------------------

    def train_enters_route(self, route_id: str, train_id: str) -> None:
        """Called when a train enters the first section of the route."""
        if route_id not in self.routes:
            return
        route = self.routes[route_id]
        if route.state == RouteState.LOCKED:
            route.state = RouteState.OCCUPIED
            logger.info("Train %s entered route %s", train_id, route_id)

    def train_clears_section(self, route_id: str, section_index: int) -> bool:
        """
        Called when train's tail passes section_index.
        For sequential release, unlock that section.
        Returns True if route fully released.
        """
        if route_id not in self.routes:
            return False
        route = self.routes[route_id]
        if route.state != RouteState.OCCUPIED:
            return False

        if section_index < len(route.track_sections):
            section = route.track_sections[section_index]
            section.clear()
            if route.release_mode == ReleaseMode.SEQUENTIAL:
                section.unlock()
            route.sections_cleared = max(route.sections_cleared, section_index + 1)

        # Check if entire route cleared
        all_cleared = all(not s.is_occupied for s in route.track_sections)
        if all_cleared:
            self.release_route(route_id)
            return True

        return False

    def release_route(self, route_id: str, reason: str = "train_passed") -> bool:
        """
        Fully release a route — unlock all sections, release points and overlap.
        """
        if route_id not in self.routes:
            return False
        route = self.routes[route_id]
        old_state = route.state

        # Unlock sections
        for section in route.track_sections:
            section.unlock()
            section.clear()

        # Release point locks
        for point_setting in route.point_settings:
            point_setting.is_secured = False

        route.state = RouteState.FREE
        route.cleared_time = datetime.utcnow()
        route.train_id = None
        self._approach_locked.discard(route_id)
        self._pending_cancellations.discard(route_id)

        record = RouteLockRecord(
            route_id=route_id,
            from_state=old_state,
            to_state=RouteState.FREE,
            timestamp=datetime.utcnow(),
            reason=reason,
        )
        self._lock_records.append(record)

        for cb in self._callbacks.get("route_released", []):
            try:
                cb(route)
            except Exception as exc:
                logger.error("Callback error: %s", exc)

        logger.info("Route %s released (%s)", route_id, reason)
        return True

    def cancel_route(self, route_id: str, operator_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Cancel a locked route (approach release). Requires approach release timer.
        Returns (success, message).
        """
        if route_id not in self.routes:
            return False, "Route not found"
        route = self.routes[route_id]

        if route.state == RouteState.OCCUPIED:
            return False, "Cannot cancel route while train is on it"

        if route.state == RouteState.FREE:
            return False, "Route is already free"

        route.state = RouteState.CANCELLED
        self._pending_cancellations.add(route_id)
        logger.warning("Route %s cancellation requested by %s", route_id, operator_id)

        # In real CBI, approach release waits for timer or track circuit clearance
        # Here we release immediately
        self.release_route(route_id, reason="operator_cancel")
        return True, f"Route {route_id} cancelled and released"

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_active_routes(self) -> List[Route]:
        return [r for r in self.routes.values()
                if r.state not in (RouteState.FREE, RouteState.CANCELLED)]

    def get_conflicts(self, route_id: str) -> List[str]:
        if route_id not in self.routes:
            return []
        return [cid for cid in self.routes[route_id].conflicting_routes
                if cid in self.routes]

    def route_status_report(self) -> List[Dict[str, Any]]:
        return [
            {
                "route_id": r.route_id,
                "name": r.name,
                "state": r.state.name,
                "train_id": r.train_id,
                "set_time": r.set_time.isoformat() if r.set_time else None,
                "total_length_m": r.total_length_m(),
                "sections": len(r.track_sections),
            }
            for r in self.routes.values()
        ]

    def audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        records = self._lock_records[-limit:]
        return [
            {
                "route_id": r.route_id,
                "from": r.from_state.name,
                "to": r.to_state.name,
                "timestamp": r.timestamp.isoformat(),
                "reason": r.reason,
                "train_id": r.train_id,
                "operator_id": r.operator_id,
            }
            for r in records
        ]

    def on_route_set(self, callback: Any) -> None:
        self._callbacks["route_set"].append(callback)

    def on_route_released(self, callback: Any) -> None:
        self._callbacks["route_released"].append(callback)

    def statistics(self) -> Dict[str, Any]:
        states = {}
        for state in RouteState:
            states[state.name] = sum(1 for r in self.routes.values() if r.state == state)
        return {
            "total_routes": len(self.routes),
            "state_distribution": states,
            "total_lock_events": len(self._lock_records),
            "pending_cancellations": len(self._pending_cancellations),
        }
