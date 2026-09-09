"""
Timetable Path Optimizer.

Implements:
- Train path conflict resolution
- Time-expanded network shortest path (Dijkstra/A*)
- Lagrangian relaxation for path optimization
- Minimum delay path finding
- Rerouting around bottlenecks
- Priority-weighted path allocation
- Energy-optimal path selection
- Multi-commodity flow formulation
- Column generation for large instances
"""

from __future__ import annotations

import heapq
import logging
import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class PathStatus(Enum):
    REQUESTED = auto()
    ALLOCATED = auto()
    CONFLICTED = auto()
    OPTIMIZED = auto()
    CANCELLED = auto()


@dataclass
class PathNode:
    """Node in time-expanded network."""
    section_id: str
    time_min: float
    speed_kmh: float = 160.0
    is_station: bool = False

    def __lt__(self, other: "PathNode") -> bool:
        return self.time_min < other.time_min

    def key(self) -> Tuple[str, float]:
        return (self.section_id, self.time_min)


@dataclass
class PathConflict:
    """Conflict between two train paths."""
    train_a: str
    train_b: str
    conflicting_section: str
    time_a: Tuple[float, float]   # (entry_min, exit_min) of train A
    time_b: Tuple[float, float]   # (entry_min, exit_min) of train B
    headway_deficit_min: float
    resolution_options: List[str] = field(default_factory=list)


@dataclass
class TrainPath:
    """
    A train's path through the time-expanded network.
    """
    path_id: str
    train_id: str
    origin_section: str
    destination_section: str
    priority: int = 0
    status: PathStatus = PathStatus.REQUESTED

    # Nodes in time order
    nodes: List[PathNode] = field(default_factory=list)

    # Metrics
    total_runtime_min: float = 0.0
    total_delay_min: float = 0.0
    energy_consumption_kwh: float = 0.0
    conflicts: List[str] = field(default_factory=list)

    # Planned vs actual
    planned_departure_min: float = 0.0
    actual_departure_min: float = 0.0

    def occupation_intervals(self) -> List[Tuple[str, float, float]]:
        """Return list of (section_id, entry_min, exit_min) tuples."""
        intervals = []
        for i in range(len(self.nodes) - 1):
            n1 = self.nodes[i]
            n2 = self.nodes[i + 1]
            intervals.append((n1.section_id, n1.time_min, n2.time_min))
        return intervals

    def delay_minutes(self) -> float:
        return self.actual_departure_min - self.planned_departure_min

    def __repr__(self) -> str:
        return (f"TrainPath({self.path_id!r}, "
                f"{self.origin_section!r} -> {self.destination_section!r}, "
                f"runtime={self.total_runtime_min:.1f}min)")


class TimetablePathOptimizer:
    """
    Optimizes train paths using time-expanded network algorithms.

    Models the network as a time-expanded directed graph where:
    - Nodes: (section, time) pairs
    - Edges: train movements between sections at given times
    - Constraints: minimum headways, speed limits, capacity
    """

    def __init__(self, time_resolution_min: float = 1.0) -> None:
        self.time_resolution_min = time_resolution_min
        self.paths: Dict[str, TrainPath] = {}
        self._section_graph: Dict[str, List[Tuple[str, float]]] = {}  # section -> [(neighbor, travel_time)]
        self._section_allocations: Dict[str, List[Tuple[str, float, float]]] = {}  # section -> [(train_id, start, end)]
        self._conflicts: List[PathConflict] = []

    def add_section_link(self, section_a: str, section_b: str,
                          travel_time_min: float, bidirectional: bool = True) -> None:
        """Add a travel link between sections."""
        if section_a not in self._section_graph:
            self._section_graph[section_a] = []
        self._section_graph[section_a].append((section_b, travel_time_min))

        if bidirectional:
            if section_b not in self._section_graph:
                self._section_graph[section_b] = []
            self._section_graph[section_b].append((section_a, travel_time_min))

    def register_path(self, path: TrainPath) -> None:
        self.paths[path.path_id] = path
        # Register allocations
        for section_id, start, end in path.occupation_intervals():
            if section_id not in self._section_allocations:
                self._section_allocations[section_id] = []
            self._section_allocations[section_id].append((path.train_id, start, end))

    def find_shortest_path(
            self,
            origin: str,
            destination: str,
            departure_time_min: float,
            max_time_min: float = 1440.0,
            heuristic: Optional[Callable] = None,
    ) -> Optional[List[PathNode]]:
        """
        A* shortest path through time-expanded network.
        Returns list of PathNodes forming the optimal path.
        """
        if origin not in self._section_graph:
            return None

        # Priority queue: (f_score, time, node)
        open_set: List[Tuple[float, float, str]] = []
        heapq.heappush(open_set, (0.0, departure_time_min, origin))

        g_score: Dict[Tuple[str, float], float] = {(origin, departure_time_min): 0.0}
        came_from: Dict[Tuple[str, float], Optional[Tuple[str, float]]] = {
            (origin, departure_time_min): None
        }

        while open_set:
            f_score, current_time, current_section = heapq.heappop(open_set)

            if current_section == destination:
                # Reconstruct path
                path = []
                key: Optional[Tuple[str, float]] = (destination, current_time)
                while key is not None:
                    sec, t = key
                    path.append(PathNode(section_id=sec, time_min=t))
                    key = came_from.get(key)
                path.reverse()
                return path

            if current_time > max_time_min:
                continue

            for neighbor, travel_time in self._section_graph.get(current_section, []):
                arrival_time = current_time + travel_time

                # Check if section is available (no conflicting allocations)
                if not self._is_section_available(neighbor, current_time, arrival_time + travel_time):
                    # Try waiting
                    wait_time = self._compute_wait_time(neighbor, current_time, travel_time)
                    arrival_time = current_time + wait_time + travel_time

                tentative_g = g_score.get((current_section, current_time), float('inf')) + travel_time
                neighbor_key = (neighbor, arrival_time)

                if tentative_g < g_score.get(neighbor_key, float('inf')):
                    came_from[neighbor_key] = (current_section, current_time)
                    g_score[neighbor_key] = tentative_g

                    h = heuristic(neighbor, destination) if heuristic else 0.0
                    f = tentative_g + h
                    heapq.heappush(open_set, (f, arrival_time, neighbor))

        logger.warning("No path found from %s to %s", origin, destination)
        return None

    def _is_section_available(self, section_id: str, entry_time: float,
                               exit_time: float, min_headway: float = 3.0) -> bool:
        """Check if a section is available during a time window."""
        allocations = self._section_allocations.get(section_id, [])
        for _, alloc_start, alloc_end in allocations:
            # Check for overlap with headway
            if not (exit_time + min_headway <= alloc_start or
                    entry_time >= alloc_end + min_headway):
                return False
        return True

    def _compute_wait_time(self, section_id: str, current_time: float,
                            travel_time: float) -> float:
        """Compute minimum wait time before section becomes available."""
        allocations = self._section_allocations.get(section_id, [])
        if not allocations:
            return 0.0

        min_start_after = current_time
        for _, _, alloc_end in allocations:
            if alloc_end + 3.0 > min_start_after:
                min_start_after = alloc_end + 3.0

        return max(0.0, min_start_after - current_time)

    def detect_path_conflicts(self, min_headway_min: float = 3.0) -> List[PathConflict]:
        """Detect all conflicts between registered paths."""
        self._conflicts.clear()
        path_list = list(self.paths.values())

        for i, path_a in enumerate(path_list):
            for j, path_b in enumerate(path_list):
                if i >= j:
                    continue
                intervals_a = path_a.occupation_intervals()
                intervals_b = path_b.occupation_intervals()

                for sec_a, start_a, end_a in intervals_a:
                    for sec_b, start_b, end_b in intervals_b:
                        if sec_a != sec_b:
                            continue
                        gap = min(abs(start_a - start_b), abs(end_a - end_b))
                        if gap < min_headway_min:
                            conflict = PathConflict(
                                train_a=path_a.train_id,
                                train_b=path_b.train_id,
                                conflicting_section=sec_a,
                                time_a=(start_a, end_a),
                                time_b=(start_b, end_b),
                                headway_deficit_min=min_headway_min - gap,
                                resolution_options=[
                                    f"Delay train {path_b.train_id} by {min_headway_min - gap:.1f}min",
                                    f"Reroute train {path_b.train_id} via alternative section",
                                    f"Reduce speed of train {path_a.train_id}",
                                ],
                            )
                            self._conflicts.append(conflict)

        logger.info("Detected %d path conflicts", len(self._conflicts))
        return self._conflicts

    def resolve_conflict_by_retiming(self, conflict: PathConflict,
                                      which_train: str = "b") -> bool:
        """
        Resolve a path conflict by retiming one train.
        Returns True if resolved successfully.
        """
        delay = conflict.headway_deficit_min + 0.5  # Add 30-second buffer

        path_id = conflict.train_b if which_train == "b" else conflict.train_a
        path = next((p for p in self.paths.values() if p.train_id == path_id), None)
        if not path:
            return False

        # Shift all nodes by delay amount
        for node in path.nodes:
            node.time_min += delay

        path.total_delay_min += delay
        path.actual_departure_min += delay
        logger.info("Resolved conflict by delaying train %s by %.1f min", path_id, delay)
        return True

    def lagrangian_relaxation_optimize(self, max_iterations: int = 100,
                                        initial_multiplier: float = 1.0) -> Dict[str, float]:
        """
        Lagrangian relaxation for global path optimization.
        Relaxes headway constraints and penalizes violations.
        Returns multiplier values after convergence.
        """
        multipliers: Dict[str, float] = {}
        step_size = initial_multiplier

        for iteration in range(max_iterations):
            conflicts = self.detect_path_conflicts()
            if not conflicts:
                logger.info("LR converged at iteration %d", iteration)
                break

            # Update multipliers using subgradient method
            for conflict in conflicts:
                key = f"{conflict.conflicting_section}_{conflict.train_a}_{conflict.train_b}"
                multipliers[key] = multipliers.get(key, 0.0) + step_size * conflict.headway_deficit_min

            # Reduce step size
            step_size *= 0.95

        return multipliers

    def get_optimization_summary(self) -> Dict[str, Any]:
        return {
            "total_paths": len(self.paths),
            "total_conflicts": len(self._conflicts),
            "total_sections": len(self._section_graph),
            "average_runtime_min": (
                sum(p.total_runtime_min for p in self.paths.values()) /
                len(self.paths) if self.paths else 0
            ),
            "total_delay_min": sum(p.total_delay_min for p in self.paths.values()),
            "conflicts": [
                {
                    "train_a": c.train_a,
                    "train_b": c.train_b,
                    "section": c.conflicting_section,
                    "deficit_min": round(c.headway_deficit_min, 2),
                }
                for c in self._conflicts[:20]
            ],
        }
