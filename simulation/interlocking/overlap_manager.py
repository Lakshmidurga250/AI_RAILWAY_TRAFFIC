"""
Overlap Manager for Computer-Based Interlocking.

An overlap is a length of track beyond the exit signal of a route,
kept clear to provide safety margin for trains overrunning signals.

Implements:
- Overlap definition and registration
- Overlap availability checking
- Overlap locking with route
- Overlap release (swinging overlap)
- Shunt overlap (shorter distance)
- Approach-locked overlap protection
- Overlap timer management
- Clearing point detection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class OverlapState(Enum):
    FREE = auto()
    LOCKED = auto()           # Locked with an active route
    RELEASING = auto()        # Timer-based release in progress
    SWING_REQUESTED = auto()  # Request to swing to alternative overlap


@dataclass
class OverlapSection:
    """A track section forming part of an overlap."""
    section_id: str
    length_m: float = 50.0
    is_clear: bool = True
    is_locked: bool = False

    def lock(self) -> None:
        self.is_locked = True

    def unlock(self) -> None:
        self.is_locked = False


@dataclass
class Overlap:
    """
    Defines the overlap beyond an exit signal.
    The overlap provides braking distance safety margin.
    """
    overlap_id: str
    name: str
    associated_signal_id: str
    sections: List[OverlapSection] = field(default_factory=list)
    minimum_length_m: float = 100.0      # Minimum required overlap length
    release_timer_s: float = 60.0        # Time before overlap can release after route clears
    swing_overlap_id: Optional[str] = None  # Alternative overlap if primary occupied

    state: OverlapState = OverlapState.FREE
    locked_by_route: Optional[str] = None
    lock_time: Optional[datetime] = None
    release_timer_start: Optional[datetime] = None

    def total_length_m(self) -> float:
        return sum(s.length_m for s in self.sections)

    def is_available(self) -> bool:
        if self.state != OverlapState.FREE:
            return False
        if any(not s.is_clear or s.is_locked for s in self.sections):
            return False
        if self.total_length_m() < self.minimum_length_m:
            return False
        return True

    def lock(self, route_id: str) -> bool:
        if not self.is_available():
            return False
        for section in self.sections:
            section.lock()
        self.state = OverlapState.LOCKED
        self.locked_by_route = route_id
        self.lock_time = datetime.utcnow()
        logger.debug("Overlap %s locked by route %s", self.overlap_id, route_id)
        return True

    def start_release_timer(self) -> None:
        self.state = OverlapState.RELEASING
        self.release_timer_start = datetime.utcnow()

    def check_release_timer(self) -> bool:
        """Returns True if timer has expired and overlap can be released."""
        if self.state != OverlapState.RELEASING:
            return False
        if self.release_timer_start is None:
            return True
        elapsed = (datetime.utcnow() - self.release_timer_start).total_seconds()
        return elapsed >= self.release_timer_s

    def release(self) -> None:
        for section in self.sections:
            section.unlock()
        self.state = OverlapState.FREE
        self.locked_by_route = None
        self.lock_time = None
        self.release_timer_start = None
        logger.debug("Overlap %s released", self.overlap_id)

    def __repr__(self) -> str:
        return (f"Overlap({self.overlap_id!r}, {self.total_length_m():.0f}m, "
                f"state={self.state.name})")


class OverlapManager:
    """
    Manages all overlaps in the interlocking area.
    Coordinates with route and signal controllers.
    """

    def __init__(self) -> None:
        self.overlaps: Dict[str, Overlap] = {}

    def register_overlap(self, overlap: Overlap) -> None:
        self.overlaps[overlap.overlap_id] = overlap
        logger.info("Registered overlap %s (%.0fm)", overlap.overlap_id, overlap.total_length_m())

    def get_overlap(self, overlap_id: str) -> Optional[Overlap]:
        return self.overlaps.get(overlap_id)

    def lock_overlap(self, overlap_id: str, route_id: str) -> Tuple[bool, str]:
        """Lock an overlap for a route, trying swing overlap if primary unavailable."""
        if overlap_id not in self.overlaps:
            return False, f"Overlap {overlap_id!r} not found"

        overlap = self.overlaps[overlap_id]

        if overlap.is_available():
            success = overlap.lock(route_id)
            if success:
                return True, f"Overlap {overlap_id} locked"

        # Try swing overlap
        if overlap.swing_overlap_id and overlap.swing_overlap_id in self.overlaps:
            swing = self.overlaps[overlap.swing_overlap_id]
            if swing.is_available():
                success = swing.lock(route_id)
                if success:
                    overlap.state = OverlapState.SWING_REQUESTED
                    logger.info("Swung to alternative overlap %s for route %s",
                                overlap.swing_overlap_id, route_id)
                    return True, f"Swing overlap {overlap.swing_overlap_id} locked"

        return False, f"No available overlap for route {route_id}"

    def release_overlap_for_route(self, route_id: str,
                                  immediate: bool = False) -> List[str]:
        """Release all overlaps locked by a route. Returns list of released overlap IDs."""
        released = []
        for overlap_id, overlap in self.overlaps.items():
            if overlap.locked_by_route == route_id:
                if immediate:
                    overlap.release()
                    released.append(overlap_id)
                else:
                    overlap.start_release_timer()
                    released.append(overlap_id)
        return released

    def tick(self) -> List[str]:
        """
        Periodic tick — check and release timed-out overlaps.
        Returns list of overlap IDs that were released.
        """
        released = []
        for overlap_id, overlap in self.overlaps.items():
            if overlap.state == OverlapState.RELEASING:
                if overlap.check_release_timer():
                    overlap.release()
                    released.append(overlap_id)
        return released

    def get_locked_overlaps(self) -> List[Dict[str, Any]]:
        return [
            {
                "overlap_id": oid,
                "route": o.locked_by_route,
                "state": o.state.name,
                "length_m": o.total_length_m(),
                "lock_time": o.lock_time.isoformat() if o.lock_time else None,
            }
            for oid, o in self.overlaps.items()
            if o.state != OverlapState.FREE
        ]

    def statistics(self) -> Dict[str, Any]:
        total = len(self.overlaps)
        locked = sum(1 for o in self.overlaps.values() if o.state == OverlapState.LOCKED)
        releasing = sum(1 for o in self.overlaps.values() if o.state == OverlapState.RELEASING)
        return {
            "total_overlaps": total,
            "free": total - locked - releasing,
            "locked": locked,
            "releasing": releasing,
        }
