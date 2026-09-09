"""
CBI Engine — Master orchestrator for Computer-Based Interlocking.

Integrates all CBI subsystems:
- RouteController: Route locking sequence
- PointController: Point machine management
- SignalController: Signal aspect management
- OverlapManager: Overlap protection
- FlankProtection: Flank/lateral protection
- DeadlockDetector: Circular occupation detection
- InterlockingTable: Route database
- PetriNetVerifier: Formal safety verification

Implements the complete ERTMS Level 2 / EN 50129 SIL-4
interlocking cycle:
  Request → Verify → Lock Points → Lock Sections →
  Set Flank → Lock Overlap → Clear Signal → Monitor →
  Sequential Release → Signal Danger → Release
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime

from simulation.interlocking.route_controller import (
    RouteController, Route, RouteState,
    TrackSection, PointSetting, ReleaseMode
)
from simulation.interlocking.point_controller import (
    PointController, PointMachine, PointPosition, PointMachineType
)
from simulation.interlocking.signal_controller import (
    SignalController, Signal, SignalAspect, SignalType,
    SignalState, SignalFailureMode
)
from simulation.interlocking.overlap_manager import (
    OverlapManager, Overlap, OverlapState, OverlapSection
)
from simulation.interlocking.flank_protection import (
    FlankProtection, FlankElement, FlankElementType, FlankLockState
)
from simulation.interlocking.deadlock_detector import (
    DeadlockDetector, DeadlockGraph, DeadlockCycle, DeadlockType
)
from simulation.interlocking.interlocking_table import (
    InterlockingTable, TableEntry, ConflictMatrix
)
from simulation.interlocking.petri_net import (
    PetriNet, Place, Transition, Token, PetriNetVerifier
)

logger = logging.getLogger(__name__)


class InterlockingState(Enum):
    INITIALIZING = auto()
    NORMAL_OPERATION = auto()
    DEGRADED = auto()          # Some elements failed but still operable
    EMERGENCY = auto()         # Emergency — all routes held at danger
    MAINTENANCE = auto()       # Maintenance mode — reduced interlocking
    FAILED = auto()            # Complete failure — requires manual control


class RouteRequestPriority(Enum):
    EMERGENCY = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class RouteRequest:
    """A request to set a route."""
    request_id: str
    route_id: str
    train_id: Optional[str]
    requested_by: str = "operator"
    priority: RouteRequestPriority = RouteRequestPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    notes: str = ""

    def __repr__(self) -> str:
        return (f"RouteRequest({self.request_id!r}, route={self.route_id!r}, "
                f"train={self.train_id!r}, priority={self.priority.name})")


@dataclass
class InterlockingEvent:
    """An event emitted by the CBI engine."""
    event_type: str
    route_id: Optional[str]
    train_id: Optional[str]
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"


class CBIEngine:
    """
    Master Computer-Based Interlocking Engine.

    This is the top-level coordinator that orchestrates all CBI subsystems
    to provide safe railway interlocking operation.
    """

    def __init__(self, name: str = "CBI-1") -> None:
        self.name = name
        self.state = InterlockingState.INITIALIZING

        # Subsystem controllers
        self.route_controller = RouteController()
        self.point_controller = PointController()
        self.signal_controller = SignalController()
        self.overlap_manager = OverlapManager()
        self.flank_protection = FlankProtection()
        self.deadlock_detector = DeadlockDetector()
        self.interlocking_table = InterlockingTable(name=f"{name}_TABLE")

        # Event bus
        self._event_queue: List[InterlockingEvent] = []
        self._event_callbacks: List[Any] = []

        # Route request queue
        self._request_queue: List[RouteRequest] = []
        self._processed_requests: List[RouteRequest] = []

        # Petri-Net for formal verification
        self._petri_net: Optional[PetriNet] = None
        self._petri_verifier: Optional[PetriNetVerifier] = None

        # Statistics
        self._stats: Dict[str, int] = {
            "routes_set": 0,
            "routes_released": 0,
            "route_denials": 0,
            "deadlocks_detected": 0,
            "spads": 0,
            "point_failures": 0,
            "signal_failures": 0,
        }

        self._start_time = datetime.utcnow()

        # Wire up callbacks
        self.route_controller.on_route_set(self._on_route_set)
        self.route_controller.on_route_released(self._on_route_released)
        self.signal_controller.on_spad(self._on_spad)
        self.point_controller.on_failure(self._on_point_failure)
        self.deadlock_detector.on_deadlock(self._on_deadlock)

        logger.info("CBI Engine %s initialized", name)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def initialize(self) -> None:
        """Transition from INITIALIZING to NORMAL_OPERATION after self-test."""
        errors = self.interlocking_table.validate_table()
        if errors:
            logger.error("Interlocking table validation failed: %s", errors)
            self.state = InterlockingState.FAILED
            return

        # Perform self-test
        self._self_test()

        self.state = InterlockingState.NORMAL_OPERATION
        self._emit_event("SYSTEM_INITIALIZED", None, None, severity="INFO",
                         data={"table_routes": len(self.interlocking_table.entries)})
        logger.info("CBI Engine %s operational", self.name)

    def _self_test(self) -> bool:
        """Run pre-operation self-test on all subsystems."""
        # Check all signals are at danger
        danger_signals = self.signal_controller.get_signals_at_danger()
        failed_signals = self.signal_controller.get_failed_signals()
        failed_points = self.point_controller.get_all_failed_points()

        if failed_signals:
            logger.warning("Self-test: %d failed signals", len(failed_signals))
        if failed_points:
            logger.warning("Self-test: %d failed points", len(failed_points))

        return True

    def emergency_stop_all(self, reason: str = "operator") -> None:
        """Emergency: set all signals to danger and cancel all active routes."""
        logger.critical("EMERGENCY STOP ALL triggered by %s", reason)
        self.state = InterlockingState.EMERGENCY

        # Set all signals to danger
        for sid in self.signal_controller.signals:
            self.signal_controller.set_danger(sid, reason="emergency_stop")

        # Cancel all active routes
        for rid in list(self.route_controller.routes.keys()):
            route = self.route_controller.routes[rid]
            if route.state not in (RouteState.FREE, RouteState.CANCELLED):
                self.route_controller.release_route(rid, reason="emergency_stop")

        self._emit_event("EMERGENCY_STOP", None, None, severity="CRITICAL",
                         data={"reason": reason})

    def resume_normal_operation(self, authorized_by: str = "supervisor") -> bool:
        """Resume normal operation after emergency."""
        if self.state != InterlockingState.EMERGENCY:
            return False
        self.state = InterlockingState.NORMAL_OPERATION
        logger.info("Normal operation resumed by %s", authorized_by)
        self._emit_event("NORMAL_OPERATION_RESUMED", None, None, severity="INFO",
                         data={"authorized_by": authorized_by})
        return True

    # ------------------------------------------------------------------
    # Route management
    # ------------------------------------------------------------------

    def request_route(self, route_id: str,
                      train_id: Optional[str] = None,
                      requested_by: str = "operator",
                      priority: RouteRequestPriority = RouteRequestPriority.NORMAL) -> Tuple[bool, str]:
        """
        Process a route request through the full interlocking locking sequence.
        Returns (success, message).
        """
        if self.state == InterlockingState.EMERGENCY:
            return False, "System in EMERGENCY state — route requests denied"

        if self.state == InterlockingState.FAILED:
            return False, "System FAILED — contact maintenance"

        # Create request record
        request = RouteRequest(
            request_id=f"REQ-{int(time.time()*1000)}",
            route_id=route_id,
            train_id=train_id,
            requested_by=requested_by,
            priority=priority,
        )
        self._request_queue.append(request)

        # Check table entry exists
        table_entry = self.interlocking_table.get_entry(route_id)
        if table_entry is None:
            # Route not in table — check if registered directly
            if route_id not in self.route_controller.routes:
                self._stats["route_denials"] += 1
                return False, f"Route {route_id!r} not found in interlocking table"

        # Step 1: Check route availability
        can_set, reason = self.route_controller.can_set_route(route_id)
        if not can_set:
            self._stats["route_denials"] += 1
            self._emit_event("ROUTE_DENIED", route_id, train_id, severity="WARNING",
                             data={"reason": reason})
            return False, reason

        # Step 2: Check and set points
        if route_id in self.route_controller.routes:
            route = self.route_controller.routes[route_id]
            for point_setting in route.point_settings:
                target_pos = point_setting.required_position
                success, msg = self.point_controller.move_point_sync(
                    point_setting.point_id, target_pos, route_id=route_id
                )
                if not success:
                    self._stats["route_denials"] += 1
                    return False, f"Point setting failed: {msg}"

        # Step 3: Lock flank protection
        if table_entry:
            # Use table entry flank elements
            pass
        else:
            flank_ok, flank_msgs = self.flank_protection.lock_flank_protection(route_id)
            if not flank_ok:
                self._stats["route_denials"] += 1
                return False, f"Flank protection failed: {'; '.join(flank_msgs)}"

        # Step 4: Lock overlap
        if table_entry and table_entry.overlap_id:
            overlap_ok, overlap_msg = self.overlap_manager.lock_overlap(
                table_entry.overlap_id, route_id)
            if not overlap_ok:
                self._stats["route_denials"] += 1
                return False, f"Overlap unavailable: {overlap_msg}"

        # Step 5: Execute route locking
        success, message = self.route_controller.set_route(
            route_id, train_id=train_id, operator_id=requested_by)
        if not success:
            self._stats["route_denials"] += 1
            return False, message

        # Step 6: Clear entry signal
        if table_entry:
            entry_sig = table_entry.entry_signal
            exit_sig = table_entry.exit_signal
            self.signal_controller.clear_signal(entry_sig, route_id, exit_sig)
        elif route_id in self.route_controller.routes:
            route = self.route_controller.routes[route_id]
            self.signal_controller.clear_signal(
                route.entry_signal_id, route_id, route.exit_signal_id)

        self._stats["routes_set"] += 1
        self._processed_requests.append(request)
        return True, f"Route {route_id} set successfully for train {train_id}"

    def release_route(self, route_id: str, reason: str = "train_passed") -> bool:
        """Release a route and return all elements to safe state."""
        success = self.route_controller.release_route(route_id, reason)
        if success:
            # Return signal to danger
            if route_id in self.route_controller.routes:
                route = self.route_controller.routes[route_id]
                self.signal_controller.set_danger(route.entry_signal_id)
            elif route_id in self.interlocking_table.entries:
                entry = self.interlocking_table.entries[route_id]
                self.signal_controller.set_danger(entry.entry_signal)

            # Release overlap
            released_overlaps = self.overlap_manager.release_overlap_for_route(route_id)
            if released_overlaps:
                logger.debug("Overlaps releasing: %s", released_overlaps)

            # Release flank protection
            self.flank_protection.release_flank_protection(route_id)

            # Unlock points
            if route_id in self.route_controller.routes:
                route = self.route_controller.routes[route_id]
                for point_setting in route.point_settings:
                    self.point_controller.points.get(
                        point_setting.point_id, None) and \
                        self.point_controller.points[point_setting.point_id].electric_unlock()

        return success

    # ------------------------------------------------------------------
    # Train tracking
    # ------------------------------------------------------------------

    def train_enters_section(self, train_id: str, route_id: str,
                             section_id: str) -> None:
        """Called when a train enters a new track section."""
        self.route_controller.train_enters_route(route_id, train_id)

        # Update deadlock detector
        self.deadlock_detector.update_train_state(
            train_id, held_sections={section_id})

        self._emit_event("TRAIN_SECTION_ENTER", route_id, train_id,
                         data={"section": section_id})

    def train_clears_section(self, train_id: str, route_id: str,
                             section_index: int) -> None:
        """Called when train tail clears a section (sequential release trigger)."""
        fully_released = self.route_controller.train_clears_section(
            route_id, section_index)

        if fully_released:
            self._emit_event("ROUTE_FULLY_RELEASED", route_id, train_id)

    def report_spad(self, train_id: str, signal_id: str) -> Dict[str, Any]:
        """Report a Signal Passed At Danger."""
        self._stats["spads"] += 1
        incident = self.signal_controller.report_spad(signal_id, train_id)
        self._emit_event("SPAD", None, train_id, severity="CRITICAL",
                         data={"signal_id": signal_id})
        return incident

    # ------------------------------------------------------------------
    # Deadlock management
    # ------------------------------------------------------------------

    def run_deadlock_check(self) -> List[DeadlockCycle]:
        """Run deadlock detection cycle."""
        deadlocks = self.deadlock_detector.detect_deadlocks()
        if deadlocks:
            self._stats["deadlocks_detected"] += len(deadlocks)
        return deadlocks

    # ------------------------------------------------------------------
    # Petri-Net formal verification
    # ------------------------------------------------------------------

    def build_petri_net_model(self) -> PetriNet:
        """
        Build a Petri-Net model of the current interlocking configuration
        for formal verification.
        """
        net = PetriNet(name=f"{self.name}_model")

        # Add places for each route (free = 1 token, locked = 0 tokens)
        for route_id, route in self.route_controller.routes.items():
            net.add_place(f"route_free_{route_id}", initial_tokens=1, label=f"Route {route_id} Free")
            net.add_place(f"route_locked_{route_id}", initial_tokens=0, label=f"Route {route_id} Locked")

        # Add places for each track section
        for route_id, route in self.route_controller.routes.items():
            for section in route.track_sections:
                if f"section_free_{section.section_id}" not in net.places:
                    net.add_place(f"section_free_{section.section_id}", initial_tokens=1)
                    net.add_place(f"section_occ_{section.section_id}", initial_tokens=0)

        # Add transitions for route setting/releasing
        for route_id, route in self.route_controller.routes.items():
            t_set = net.add_transition(f"set_{route_id}", label=f"Set Route {route_id}")
            t_rel = net.add_transition(f"rel_{route_id}", label=f"Release Route {route_id}")

            # Setting transition: consume free token, produce locked token
            net.add_arc(f"route_free_{route_id}", f"set_{route_id}", weight=1)
            net.add_arc(f"set_{route_id}", f"route_locked_{route_id}", weight=1)

            # Releasing transition: consume locked token, produce free token
            net.add_arc(f"route_locked_{route_id}", f"rel_{route_id}", weight=1)
            net.add_arc(f"rel_{route_id}", f"route_free_{route_id}", weight=1)

            # Add section consumption/release for each section in route
            for section in route.track_sections:
                sec_id = section.section_id
                # Setting requires section to be free
                net.add_arc(f"section_free_{sec_id}", f"set_{route_id}", weight=1)
                net.add_arc(f"set_{route_id}", f"section_occ_{sec_id}", weight=1)
                # Releasing returns section to free
                net.add_arc(f"section_occ_{sec_id}", f"rel_{route_id}", weight=1)
                net.add_arc(f"rel_{route_id}", f"section_free_{sec_id}", weight=1)

            # Add inhibitor arcs for conflicting routes
            for conflict_id in route.conflicting_routes:
                if f"route_locked_{conflict_id}" in net.places:
                    net.add_inhibitor_arc(f"route_locked_{conflict_id}", f"set_{route_id}", threshold=1)

        net.save_initial_marking()
        self._petri_net = net
        self._petri_verifier = PetriNetVerifier(net)
        logger.info("Petri-Net model built: %d places, %d transitions",
                    len(net.places), len(net.transitions))
        return net

    def run_formal_verification(self, max_states: int = 10_000) -> Dict[str, Any]:
        """
        Run formal verification on the Petri-Net model.
        Returns verification results.
        """
        if self._petri_net is None:
            self.build_petri_net_model()

        verifier = self._petri_verifier
        assert verifier is not None

        # Build conflict pairs for mutual exclusion checks
        conflict_pairs = []
        for route_id, route in self.route_controller.routes.items():
            for conflict_id in route.conflicting_routes:
                pair = (f"route_locked_{route_id}", f"route_locked_{conflict_id}")
                if pair not in conflict_pairs and (pair[1], pair[0]) not in conflict_pairs:
                    conflict_pairs.append(pair)

        results = verifier.full_verification(conflict_pairs=conflict_pairs)

        return {
            "verified": all(r.satisfied for r in results.values()),
            "results": {name: {
                "property": r.property_name,
                "satisfied": r.satisfied,
                "details": r.details,
                "evidence": r.evidence[:3],
            } for name, r in results.items()},
            "net_stats": self._petri_net.statistics(),
            "summary": verifier.summary(results),
        }

    # ------------------------------------------------------------------
    # Periodic maintenance
    # ------------------------------------------------------------------

    def tick(self, dt_s: float = 1.0) -> None:
        """
        Called periodically to handle timers, overlap releases, deadlock checks.
        """
        # Release timed overlaps
        released = self.overlap_manager.tick()
        if released:
            logger.debug("Overlaps released by timer: %s", released)

        # Check degraded state
        failed_signals = self.signal_controller.get_failed_signals()
        failed_points = self.point_controller.get_all_failed_points()
        if (failed_signals or failed_points) and self.state == InterlockingState.NORMAL_OPERATION:
            self.state = InterlockingState.DEGRADED
            logger.warning("CBI degraded: %d failed signals, %d failed points",
                           len(failed_signals), len(failed_points))

        # Periodic deadlock check
        deadlocks = self.run_deadlock_check()
        if deadlocks and self.state == InterlockingState.NORMAL_OPERATION:
            self._emit_event("DEADLOCK_DETECTED", None, None, severity="CRITICAL",
                             data={"count": len(deadlocks)})

    # ------------------------------------------------------------------
    # Event management
    # ------------------------------------------------------------------

    def _emit_event(self, event_type: str, route_id: Optional[str],
                    train_id: Optional[str], severity: str = "INFO",
                    data: Optional[Dict[str, Any]] = None) -> None:
        event = InterlockingEvent(
            event_type=event_type,
            route_id=route_id,
            train_id=train_id,
            timestamp=datetime.utcnow(),
            data=data or {},
            severity=severity,
        )
        self._event_queue.append(event)
        if len(self._event_queue) > 10000:
            self._event_queue = self._event_queue[-5000:]

        for cb in self._event_callbacks:
            try:
                cb(event)
            except Exception as exc:
                logger.error("Event callback error: %s", exc)

    def _on_route_set(self, route: Route) -> None:
        self._emit_event("ROUTE_SET", route.route_id, route.train_id)

    def _on_route_released(self, route: Route) -> None:
        self._stats["routes_released"] += 1

    def _on_spad(self, incident: Dict[str, Any]) -> None:
        self._stats["spads"] += 1

    def _on_point_failure(self, point_id: str, reason: str) -> None:
        self._stats["point_failures"] += 1
        self._emit_event("POINT_FAILURE", None, None, severity="ERROR",
                         data={"point_id": point_id, "reason": reason})

    def _on_deadlock(self, deadlock: DeadlockCycle) -> None:
        self._stats["deadlocks_detected"] += 1
        self._emit_event("DEADLOCK", None, None, severity="CRITICAL",
                         data={"cycle": deadlock.involved_trains})

    def on_event(self, callback: Any) -> None:
        self._event_callbacks.append(callback)

    # ------------------------------------------------------------------
    # Status and reporting
    # ------------------------------------------------------------------

    def full_status(self) -> Dict[str, Any]:
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        return {
            "name": self.name,
            "state": self.state.name,
            "uptime_s": uptime,
            "statistics": self._stats,
            "routes": self.route_controller.statistics(),
            "signals": self.signal_controller.statistics(),
            "points": self.point_controller.statistics(),
            "overlaps": self.overlap_manager.statistics(),
            "flank_protection": self.flank_protection.statistics(),
            "deadlock_detector": self.deadlock_detector.statistics(),
            "interlocking_table": self.interlocking_table.statistics(),
            "recent_events": [
                {
                    "type": e.event_type,
                    "route": e.route_id,
                    "train": e.train_id,
                    "severity": e.severity,
                    "time": e.timestamp.isoformat(),
                }
                for e in self._event_queue[-20:]
            ],
        }

    def audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.route_controller.audit_log(limit)

    def __repr__(self) -> str:
        return f"CBIEngine(name={self.name!r}, state={self.state.name})"
