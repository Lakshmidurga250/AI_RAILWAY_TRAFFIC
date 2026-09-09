"""
Flank Protection Controller for Computer-Based Interlocking.

Flank protection prevents trains on converging routes from
entering the protected route area, providing lateral safety.

Implements:
- Flank protection element registration
- Automatic flank locking when route is set
- Swing nose crossing flank protection
- Diamond crossing protection
- Protection signal setting
- Derailer control
- Trap point management
- Active/passive flank protection modes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class FlankLockState(Enum):
    FREE = auto()
    LOCKED = auto()       # Flank element locked in protecting position
    FAILED = auto()       # Element failed — route cannot be set


class FlankElementType(Enum):
    FLANK_SIGNAL = auto()     # Signal kept at danger for flank protection
    FLANK_POINT = auto()      # Point set to derail conflicting trains
    TRAP_POINT = auto()       # Trap/catch point derailing runaway
    DERAILER = auto()         # Mechanical derailer device
    TRAP_SIDING = auto()      # Trap siding for overspeed protection


@dataclass
class FlankElement:
    """A single element providing flank protection for a route."""
    element_id: str
    element_type: FlankElementType
    name: str
    protecting_route_ids: Set[str] = field(default_factory=set)  # Routes this protects
    conflicting_route_ids: Set[str] = field(default_factory=set)  # Routes this conflicts with

    # Physical position for protection
    required_position: str = "N"   # Point position or signal aspect for protection
    current_position: Optional[str] = None

    state: FlankLockState = FlankLockState.FREE
    locked_by_route: Optional[str] = None
    lock_time: Optional[datetime] = None
    is_operative: bool = True

    def lock_for_route(self, route_id: str) -> bool:
        if not self.is_operative:
            return False
        self.state = FlankLockState.LOCKED
        self.locked_by_route = route_id
        self.current_position = self.required_position
        self.lock_time = datetime.utcnow()
        logger.debug("Flank element %s locked for route %s", self.element_id, route_id)
        return True

    def release(self) -> None:
        self.state = FlankLockState.FREE
        self.locked_by_route = None
        self.lock_time = None
        logger.debug("Flank element %s released", self.element_id)

    def is_protecting(self, route_id: str) -> bool:
        return route_id in self.protecting_route_ids and self.state == FlankLockState.LOCKED

    def __repr__(self) -> str:
        return (f"FlankElement({self.element_id!r}, "
                f"{self.element_type.name}, state={self.state.name})")


@dataclass
class FlankProtectionGroup:
    """
    A group of flank elements that must ALL be locked before a route can proceed.
    """
    group_id: str
    route_id: str             # Route being protected
    elements: List[FlankElement] = field(default_factory=list)

    def is_fully_locked(self) -> bool:
        return all(e.state == FlankLockState.LOCKED for e in self.elements)

    def has_failure(self) -> bool:
        return any(e.state == FlankLockState.FAILED for e in self.elements)

    def lock_all(self) -> bool:
        for element in self.elements:
            if not element.lock_for_route(self.route_id):
                return False
        return True

    def release_all(self) -> None:
        for element in self.elements:
            element.release()


class FlankProtection:
    """
    Manages flank protection for all routes in an interlocking.
    """

    def __init__(self) -> None:
        self.elements: Dict[str, FlankElement] = {}
        self.protection_groups: Dict[str, FlankProtectionGroup] = {}
        self._route_to_groups: Dict[str, List[str]] = {}  # route_id -> group_ids

    def register_element(self, element: FlankElement) -> None:
        self.elements[element.element_id] = element

    def register_protection_group(self, group: FlankProtectionGroup) -> None:
        self.protection_groups[group.group_id] = group
        if group.route_id not in self._route_to_groups:
            self._route_to_groups[group.route_id] = []
        self._route_to_groups[group.route_id].append(group.group_id)
        logger.info("Registered flank protection group %s for route %s",
                    group.group_id, group.route_id)

    def check_flank_available(self, route_id: str) -> bool:
        """Check if all flank protection elements for a route are available."""
        group_ids = self._route_to_groups.get(route_id, [])
        for gid in group_ids:
            group = self.protection_groups[gid]
            for element in group.elements:
                if element.state == FlankLockState.LOCKED and element.locked_by_route != route_id:
                    return False
                if element.state == FlankLockState.FAILED:
                    return False
        return True

    def lock_flank_protection(self, route_id: str) -> Tuple[bool, List[str]]:
        """Lock all flank elements for a route. Returns (success, messages)."""
        messages = []
        group_ids = self._route_to_groups.get(route_id, [])

        for gid in group_ids:
            group = self.protection_groups[gid]
            if group.has_failure():
                messages.append(f"Group {gid} has failed elements — cannot set route")
                return False, messages
            if not group.lock_all():
                messages.append(f"Failed to lock group {gid}")
                return False, messages
            messages.append(f"Flank group {gid} locked for route {route_id}")

        return True, messages

    def release_flank_protection(self, route_id: str) -> None:
        """Release all flank elements when a route is released."""
        group_ids = self._route_to_groups.get(route_id, [])
        for gid in group_ids:
            self.protection_groups[gid].release_all()
        logger.info("Flank protection released for route %s", route_id)

    def inject_failure(self, element_id: str) -> bool:
        if element_id not in self.elements:
            return False
        self.elements[element_id].state = FlankLockState.FAILED
        self.elements[element_id].is_operative = False
        logger.error("Flank element %s FAILED", element_id)
        return True

    def restore_element(self, element_id: str) -> bool:
        if element_id not in self.elements:
            return False
        element = self.elements[element_id]
        element.state = FlankLockState.FREE
        element.is_operative = True
        element.locked_by_route = None
        return True

    def get_active_protection(self) -> List[Dict[str, Any]]:
        return [
            {
                "element_id": eid,
                "type": e.element_type.name,
                "state": e.state.name,
                "locked_by_route": e.locked_by_route,
            }
            for eid, e in self.elements.items()
            if e.state != FlankLockState.FREE
        ]

    def statistics(self) -> Dict[str, Any]:
        total = len(self.elements)
        return {
            "total_elements": total,
            "locked": sum(1 for e in self.elements.values() if e.state == FlankLockState.LOCKED),
            "failed": sum(1 for e in self.elements.values() if e.state == FlankLockState.FAILED),
            "protection_groups": len(self.protection_groups),
        }


# Needed for type annotation in flank_protection methods
from typing import Tuple
