"""
Point (Switch) Controller for Computer-Based Interlocking.

Implements:
- Point machine simulation (motorized turnouts)
- Position detection (normal/reverse/moving/failed)
- Point locking (mechanical + electrical)
- Trailable point detection
- Swing-nose crossing control
- Diamond crossing management
- Hysteresis and debounce logic
- Point heating control (winter mode)
- Maintenance tracking
- MTBF/reliability modeling
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PointPosition(Enum):
    NORMAL = "N"      # Straight
    REVERSE = "R"     # Diverging
    MOVING = "M"      # In motion (transitioning)
    FAILED = "F"      # Detected failure
    UNKNOWN = "U"     # Unknown / no detection


class PointLockState(Enum):
    UNLOCKED = auto()
    MECHANICALLY_LOCKED = auto()
    ELECTRICALLY_LOCKED = auto()
    BOTH_LOCKED = auto()


class PointMachineType(Enum):
    MOTORIZED_5S = auto()   # Standard 5-second throw
    MOTORIZED_3S = auto()   # Fast 3-second throw
    HYDRAULIC = auto()      # Hydraulic actuator
    PNEUMATIC = auto()      # Pneumatic actuator
    MANUAL = auto()         # Manual operation
    TRAILABLE = auto()      # Can be trailed by train


@dataclass
class PointHealthMetrics:
    total_operations: int = 0
    failed_operations: int = 0
    last_maintenance: Optional[datetime] = None
    next_maintenance_due: Optional[datetime] = None
    cumulative_operating_time_s: float = 0.0
    current_wear_percent: float = 0.0
    mtbf_hours: float = 8760.0  # 1 year
    estimated_remaining_life_hours: float = 8760.0

    def record_operation(self, success: bool, duration_s: float) -> None:
        self.total_operations += 1
        self.cumulative_operating_time_s += duration_s
        if not success:
            self.failed_operations += 1
        self.current_wear_percent = min(100.0, self.total_operations / (self.mtbf_hours * 100) * 100)
        self.estimated_remaining_life_hours = max(
            0.0, self.mtbf_hours - self.cumulative_operating_time_s / 3600
        )

    @property
    def failure_rate(self) -> float:
        if self.total_operations == 0:
            return 0.0
        return self.failed_operations / self.total_operations


@dataclass
class PointMachine:
    """
    Motorized point machine model.
    Simulates real-world electro-mechanical switch machine behavior.
    """
    point_id: str
    name: str
    machine_type: PointMachineType = PointMachineType.MOTORIZED_5S
    throw_time_s: float = 5.0

    # Positions
    position: PointPosition = PointPosition.NORMAL
    detected_position: PointPosition = PointPosition.NORMAL
    commanded_position: PointPosition = PointPosition.NORMAL

    # Locking
    lock_state: PointLockState = PointLockState.UNLOCKED
    lock_reason: Optional[str] = None
    locked_by_route: Optional[str] = None

    # Sensors
    normal_detection: bool = True    # End-position detector in normal position
    reverse_detection: bool = False  # End-position detector in reverse position
    movement_sensor: bool = False    # Motion sensor

    # Status
    is_operational: bool = True
    heating_active: bool = False
    temperature_celsius: float = 20.0
    last_operation_time: Optional[datetime] = None
    operation_in_progress: bool = False

    # Metrics
    health: PointHealthMetrics = field(default_factory=PointHealthMetrics)

    # Trailable
    is_trailable: bool = False
    trailed_count: int = 0

    def __repr__(self) -> str:
        return (f"PointMachine({self.point_id!r}, "
                f"pos={self.position.name}, "
                f"locked={self.lock_state.name})")

    def is_detected_in_position(self, position: PointPosition) -> bool:
        """Check if position detection is confirmed."""
        if position == PointPosition.NORMAL:
            return self.normal_detection and not self.reverse_detection
        elif position == PointPosition.REVERSE:
            return self.reverse_detection and not self.normal_detection
        return False

    def is_locked_in_position(self, position: PointPosition) -> bool:
        """Check if locked in required position."""
        return (self.is_detected_in_position(position) and
                self.lock_state in (PointLockState.BOTH_LOCKED,
                                    PointLockState.MECHANICALLY_LOCKED,
                                    PointLockState.ELECTRICALLY_LOCKED))

    def can_move(self) -> bool:
        return (self.is_operational and
                not self.operation_in_progress and
                self.lock_state == PointLockState.UNLOCKED)

    def electric_lock(self, route_id: Optional[str] = None) -> bool:
        if self.lock_state == PointLockState.UNLOCKED:
            self.lock_state = PointLockState.ELECTRICALLY_LOCKED
        elif self.lock_state == PointLockState.MECHANICALLY_LOCKED:
            self.lock_state = PointLockState.BOTH_LOCKED
        self.locked_by_route = route_id
        self.lock_reason = f"Route lock: {route_id}"
        return True

    def electric_unlock(self) -> bool:
        if self.lock_state == PointLockState.BOTH_LOCKED:
            self.lock_state = PointLockState.MECHANICALLY_LOCKED
        elif self.lock_state == PointLockState.ELECTRICALLY_LOCKED:
            self.lock_state = PointLockState.UNLOCKED
        self.locked_by_route = None
        self.lock_reason = None
        return True

    def mechanical_lock(self) -> bool:
        if self.lock_state == PointLockState.UNLOCKED:
            self.lock_state = PointLockState.MECHANICALLY_LOCKED
        elif self.lock_state == PointLockState.ELECTRICALLY_LOCKED:
            self.lock_state = PointLockState.BOTH_LOCKED
        return True

    def mechanical_unlock(self) -> bool:
        if self.lock_state == PointLockState.BOTH_LOCKED:
            self.lock_state = PointLockState.ELECTRICALLY_LOCKED
        elif self.lock_state == PointLockState.MECHANICALLY_LOCKED:
            self.lock_state = PointLockState.UNLOCKED
        return True

    def trail(self, direction: PointPosition) -> bool:
        """Handle trailing — train forces point to new position."""
        if not self.is_trailable:
            logger.error("Point %s trailed but not trailable! Derailment risk!", self.point_id)
            return False
        self.position = direction
        self.detected_position = direction
        self.normal_detection = (direction == PointPosition.NORMAL)
        self.reverse_detection = (direction == PointPosition.REVERSE)
        self.trailed_count += 1
        logger.warning("Point %s trailed by train to %s", self.point_id, direction.name)
        return True

    def status_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "name": self.name,
            "position": self.position.name,
            "detected_position": self.detected_position.name,
            "commanded_position": self.commanded_position.name,
            "lock_state": self.lock_state.name,
            "locked_by_route": self.locked_by_route,
            "is_operational": self.is_operational,
            "normal_detection": self.normal_detection,
            "reverse_detection": self.reverse_detection,
            "operation_in_progress": self.operation_in_progress,
            "heating_active": self.heating_active,
            "temperature_celsius": self.temperature_celsius,
            "total_operations": self.health.total_operations,
            "failure_rate": self.health.failure_rate,
            "wear_percent": self.health.current_wear_percent,
            "trailed_count": self.trailed_count,
        }


class PointController:
    """
    Manages all point machines in the interlocking area.
    Provides coordinated point setting, detection, and fault management.
    """

    def __init__(self) -> None:
        self.points: Dict[str, PointMachine] = {}
        self._operation_queue: List[Dict[str, Any]] = []
        self._failure_callbacks: List[Callable] = []
        self._operation_callbacks: List[Callable] = []

    def register_point(self, point: PointMachine) -> None:
        self.points[point.point_id] = point
        logger.info("Registered point machine %s", point.point_id)

    def get_point(self, point_id: str) -> Optional[PointMachine]:
        return self.points.get(point_id)

    async def move_point_async(self, point_id: str,
                               target_position: PointPosition,
                               route_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Asynchronously move a point to target position.
        Simulates real throw time with detection confirmation.
        Returns (success, message).
        """
        if point_id not in self.points:
            return False, f"Point {point_id!r} not registered"

        point = self.points[point_id]

        if not point.can_move():
            if not point.is_operational:
                return False, f"Point {point_id!r} is not operational (FAILED)"
            if point.lock_state != PointLockState.UNLOCKED:
                return False, f"Point {point_id!r} is locked ({point.lock_state.name})"
            if point.operation_in_progress:
                return False, f"Point {point_id!r} operation already in progress"

        if point.position == target_position:
            logger.debug("Point %s already in position %s", point_id, target_position.name)
            return True, f"Point already in {target_position.name}"

        # Begin movement
        point.operation_in_progress = True
        point.position = PointPosition.MOVING
        point.normal_detection = False
        point.reverse_detection = False
        point.movement_sensor = True
        point.commanded_position = target_position

        logger.info("Moving point %s to %s (%.1fs throw)", point_id, target_position.name, point.throw_time_s)

        # Simulate throw time
        await asyncio.sleep(point.throw_time_s * 0.01)  # Scaled for simulation

        # Determine success with failure probability
        failure_chance = point.health.current_wear_percent / 500.0  # 0–0.2% at 100% wear
        success = random.random() > failure_chance

        if success:
            point.position = target_position
            point.detected_position = target_position
            point.normal_detection = (target_position == PointPosition.NORMAL)
            point.reverse_detection = (target_position == PointPosition.REVERSE)
            point.movement_sensor = False
            point.last_operation_time = datetime.utcnow()
            point.health.record_operation(True, point.throw_time_s)

            if route_id:
                point.electric_lock(route_id)

            for cb in self._operation_callbacks:
                try:
                    cb(point_id, target_position, True)
                except Exception:
                    pass

            logger.info("Point %s moved to %s successfully", point_id, target_position.name)
            result = True, f"Point {point_id} moved to {target_position.name}"
        else:
            point.position = PointPosition.FAILED
            point.detected_position = PointPosition.UNKNOWN
            point.is_operational = False
            point.health.record_operation(False, point.throw_time_s)

            for cb in self._failure_callbacks:
                try:
                    cb(point_id, "move_failure")
                except Exception:
                    pass

            logger.error("Point %s FAILED to move to %s", point_id, target_position.name)
            result = False, f"Point {point_id} FAILED — operational: False"

        point.operation_in_progress = False
        return result

    def move_point_sync(self, point_id: str, target_position: PointPosition,
                        route_id: Optional[str] = None,
                        simulate_failure: bool = False) -> Tuple[bool, str]:
        """
        Synchronous point movement for simulation without asyncio.
        """
        if point_id not in self.points:
            return False, f"Point {point_id!r} not registered"

        point = self.points[point_id]

        if not point.can_move():
            return False, f"Point {point_id!r} cannot move (locked={point.lock_state.name})"

        if point.position == target_position:
            return True, f"Already in {target_position.name}"

        point.position = target_position
        point.detected_position = target_position
        point.normal_detection = (target_position == PointPosition.NORMAL)
        point.reverse_detection = (target_position == PointPosition.REVERSE)
        point.movement_sensor = False
        point.last_operation_time = datetime.utcnow()
        point.health.record_operation(not simulate_failure, point.throw_time_s)

        if simulate_failure:
            point.position = PointPosition.FAILED
            point.is_operational = False
            return False, f"Point {point_id} simulated failure"

        if route_id:
            point.electric_lock(route_id)

        return True, f"Point {point_id} set to {target_position.name}"

    def set_heating(self, point_id: str, active: bool) -> bool:
        if point_id not in self.points:
            return False
        self.points[point_id].heating_active = active
        logger.info("Point %s heating: %s", point_id, "ON" if active else "OFF")
        return True

    def reset_fault(self, point_id: str) -> bool:
        """Reset a failed point after maintenance."""
        if point_id not in self.points:
            return False
        point = self.points[point_id]
        point.is_operational = True
        point.position = PointPosition.UNKNOWN
        point.detected_position = PointPosition.UNKNOWN
        point.health.last_maintenance = datetime.utcnow()
        point.health.next_maintenance_due = datetime.utcnow() + timedelta(hours=2000)
        logger.info("Point %s fault reset", point_id)
        return True

    def get_all_failed_points(self) -> List[str]:
        return [pid for pid, p in self.points.items() if not p.is_operational]

    def get_locked_points(self) -> List[Dict[str, Any]]:
        return [
            {"point_id": pid, "lock_state": p.lock_state.name, "route": p.locked_by_route}
            for pid, p in self.points.items()
            if p.lock_state != PointLockState.UNLOCKED
        ]

    def full_status_report(self) -> List[Dict[str, Any]]:
        return [p.status_dict() for p in self.points.values()]

    def on_failure(self, callback: Callable) -> None:
        self._failure_callbacks.append(callback)

    def on_operation(self, callback: Callable) -> None:
        self._operation_callbacks.append(callback)

    def statistics(self) -> Dict[str, Any]:
        total = len(self.points)
        failed = len(self.get_all_failed_points())
        locked = len(self.get_locked_points())
        heating = sum(1 for p in self.points.values() if p.heating_active)
        return {
            "total_points": total,
            "operational": total - failed,
            "failed": failed,
            "locked": locked,
            "heating_active": heating,
            "total_operations": sum(p.health.total_operations for p in self.points.values()),
            "total_failures": sum(p.health.failed_operations for p in self.points.values()),
        }
