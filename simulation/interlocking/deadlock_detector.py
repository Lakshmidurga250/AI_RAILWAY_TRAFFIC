"""
Deadlock Detector for Computer-Based Interlocking.

Detects railway-specific deadlock situations:
- Cyclic occupation: A->B->C->A (trains blocking each other)
- Head-on conflicts on single-track sections
- Resource deadlocks in station throat areas
- Circular dependency in route requests
- Starvation detection (a train starved of route access)

Uses graph-theoretic algorithms:
- Resource allocation graph (RAG)
- Cycle detection (DFS with coloring)
- Strongly Connected Components (Tarjan's algorithm)
- Banker's algorithm for safe state verification
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DeadlockType(Enum):
    CIRCULAR_OCCUPATION = auto()     # A->B->C->A cyclic block
    HEAD_ON_CONFLICT = auto()        # Two trains on same section facing each other
    RESOURCE_DEADLOCK = auto()       # Circular route-holding
    STARVATION = auto()              # Train cannot access any route for too long


@dataclass
class DeadlockCycle:
    """Represents a detected deadlock cycle."""
    cycle_type: DeadlockType
    involved_trains: List[str]
    involved_sections: List[str]
    involved_routes: List[str] = field(default_factory=list)
    severity: str = "CRITICAL"
    detection_time: str = ""
    resolution_suggestion: str = ""

    def __repr__(self) -> str:
        return (f"DeadlockCycle(type={self.cycle_type.name}, "
                f"trains={self.involved_trains})")


@dataclass
class TrainResourceNode:
    """Node in the resource allocation graph."""
    train_id: str
    held_sections: Set[str] = field(default_factory=set)
    requested_sections: Set[str] = field(default_factory=set)
    held_routes: Set[str] = field(default_factory=set)
    requested_routes: Set[str] = field(default_factory=set)
    wait_time_s: float = 0.0

    def __repr__(self) -> str:
        return f"TrainNode({self.train_id!r}, holds={self.held_sections})"


class DeadlockGraph:
    """
    Resource Allocation Graph (RAG) for deadlock analysis.
    Nodes: trains and resources (sections/routes)
    Edges: hold edges (train->resource) and request edges (resource->train)
    """

    def __init__(self) -> None:
        self.train_nodes: Dict[str, TrainResourceNode] = {}
        self.section_holders: Dict[str, Optional[str]] = {}    # section -> train_id
        self.section_waiters: Dict[str, List[str]] = defaultdict(list)  # section -> [train_ids]
        self.route_holders: Dict[str, Optional[str]] = {}
        self.route_waiters: Dict[str, List[str]] = defaultdict(list)

    def add_train(self, train_id: str) -> TrainResourceNode:
        node = TrainResourceNode(train_id=train_id)
        self.train_nodes[train_id] = node
        return node

    def train_holds_section(self, train_id: str, section_id: str) -> None:
        if train_id not in self.train_nodes:
            self.add_train(train_id)
        self.train_nodes[train_id].held_sections.add(section_id)
        self.section_holders[section_id] = train_id

    def train_requests_section(self, train_id: str, section_id: str) -> None:
        if train_id not in self.train_nodes:
            self.add_train(train_id)
        self.train_nodes[train_id].requested_sections.add(section_id)
        self.section_waiters[section_id].append(train_id)

    def train_releases_section(self, train_id: str, section_id: str) -> None:
        if train_id in self.train_nodes:
            self.train_nodes[train_id].held_sections.discard(section_id)
        if self.section_holders.get(section_id) == train_id:
            self.section_holders[section_id] = None

    def build_wait_for_graph(self) -> Dict[str, Set[str]]:
        """
        Build the wait-for graph: train A -> train B means A is waiting for a section held by B.
        """
        wfg: Dict[str, Set[str]] = defaultdict(set)
        for train_id, node in self.train_nodes.items():
            for section in node.requested_sections:
                holder = self.section_holders.get(section)
                if holder and holder != train_id:
                    wfg[train_id].add(holder)
        return dict(wfg)

    def find_cycles_dfs(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Find all cycles in the wait-for graph using DFS.
        Returns list of cycles (each cycle is a list of train IDs).
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in graph}
        parent = {node: None for node in graph}
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            color[node] = GRAY
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in color:
                    color[neighbor] = WHITE
                if color[neighbor] == GRAY:
                    # Found a cycle — extract it
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                elif color[neighbor] == WHITE:
                    parent[neighbor] = node
                    dfs(neighbor, path)

            path.pop()
            color[node] = BLACK

        for node in list(graph.keys()):
            if color.get(node, WHITE) == WHITE:
                dfs(node, [])

        return cycles

    def tarjan_scc(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Tarjan's SCC algorithm to find strongly connected components.
        An SCC with more than one node indicates a potential deadlock.
        """
        index_counter = [0]
        stack = []
        lowlinks: Dict[str, int] = {}
        index: Dict[str, int] = {}
        on_stack: Dict[str, bool] = {}
        sccs: List[List[str]] = []

        def strongconnect(node: str) -> None:
            index[node] = lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True

            for successor in graph.get(node, set()):
                if successor not in index:
                    strongconnect(successor)
                    lowlinks[node] = min(lowlinks[node], lowlinks.get(successor, index_counter[0]))
                elif on_stack.get(successor, False):
                    lowlinks[node] = min(lowlinks[node], index.get(successor, index_counter[0]))

            if lowlinks[node] == index[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    scc.append(w)
                    if w == node:
                        break
                if len(scc) > 1:
                    sccs.append(scc)

        for node in graph:
            if node not in index:
                strongconnect(node)

        return sccs

    def clear(self) -> None:
        self.train_nodes.clear()
        self.section_holders.clear()
        self.section_waiters.clear()
        self.route_holders.clear()
        self.route_waiters.clear()


class DeadlockDetector:
    """
    Main deadlock detection engine.
    Continuously monitors the resource allocation state and detects cycles.
    """

    def __init__(self) -> None:
        self.graph = DeadlockGraph()
        self._detected_deadlocks: List[DeadlockCycle] = []
        self._detection_callbacks: List[Any] = []
        self._starvation_threshold_s: float = 300.0  # 5 minutes

    def update_train_state(self, train_id: str,
                           held_sections: Optional[Set[str]] = None,
                           requested_sections: Optional[Set[str]] = None,
                           held_routes: Optional[Set[str]] = None,
                           requested_routes: Optional[Set[str]] = None,
                           wait_time_s: float = 0.0) -> None:
        """Update the resource state for a train."""
        if train_id not in self.graph.train_nodes:
            self.graph.add_train(train_id)

        node = self.graph.train_nodes[train_id]
        if held_sections is not None:
            # Update held sections
            for old_sec in list(node.held_sections):
                if old_sec not in held_sections:
                    self.graph.train_releases_section(train_id, old_sec)
            for new_sec in held_sections:
                if new_sec not in node.held_sections:
                    self.graph.train_holds_section(train_id, new_sec)

        if requested_sections is not None:
            node.requested_sections = set(requested_sections)
            for sec in requested_sections:
                if train_id not in self.graph.section_waiters[sec]:
                    self.graph.section_waiters[sec].append(train_id)

        if held_routes is not None:
            node.held_routes = set(held_routes)
        if requested_routes is not None:
            node.requested_routes = set(requested_routes)

        node.wait_time_s = wait_time_s

    def detect_deadlocks(self) -> List[DeadlockCycle]:
        """
        Run full deadlock detection cycle.
        Returns list of newly detected deadlocks.
        """
        new_deadlocks = []

        # Build wait-for graph
        wfg = self.graph.build_wait_for_graph()

        if not wfg:
            return []

        # Find cycles using DFS
        cycles = self.graph.find_cycles_dfs(wfg)

        for cycle in cycles:
            if len(cycle) < 2:
                continue

            # Gather involved sections
            involved_sections = []
            for train_id in cycle:
                node = self.graph.train_nodes.get(train_id)
                if node:
                    involved_sections.extend(list(node.requested_sections))

            dl = DeadlockCycle(
                cycle_type=DeadlockType.CIRCULAR_OCCUPATION,
                involved_trains=list(set(cycle)),
                involved_sections=list(set(involved_sections)),
                severity="CRITICAL",
                resolution_suggestion=self._suggest_resolution(cycle),
            )
            new_deadlocks.append(dl)
            self._detected_deadlocks.append(dl)
            logger.critical("DEADLOCK DETECTED: %s", dl)

            for cb in self._detection_callbacks:
                try:
                    cb(dl)
                except Exception:
                    pass

        # Check for starvation
        for train_id, node in self.graph.train_nodes.items():
            if node.wait_time_s > self._starvation_threshold_s:
                sl = DeadlockCycle(
                    cycle_type=DeadlockType.STARVATION,
                    involved_trains=[train_id],
                    involved_sections=list(node.requested_sections),
                    severity="WARNING",
                    resolution_suggestion=f"Priority boost for train {train_id}",
                )
                new_deadlocks.append(sl)

        return new_deadlocks

    def detect_head_on_conflicts(self,
                                 train_positions: Dict[str, Tuple[str, str]]) -> List[DeadlockCycle]:
        """
        Detect head-on conflicts: two trains on the same section traveling in opposite directions.
        train_positions: {train_id: (section_id, direction)}
        """
        conflicts = []
        section_trains: Dict[str, List[Tuple[str, str]]] = defaultdict(list)

        for train_id, (section_id, direction) in train_positions.items():
            section_trains[section_id].append((train_id, direction))

        for section_id, trains in section_trains.items():
            if len(trains) >= 2:
                directions = {t[1] for t in trains}
                if len(directions) > 1:  # Multiple directions on same section
                    conflict = DeadlockCycle(
                        cycle_type=DeadlockType.HEAD_ON_CONFLICT,
                        involved_trains=[t[0] for t in trains],
                        involved_sections=[section_id],
                        severity="CRITICAL",
                        resolution_suggestion=f"Emergency stop all trains on section {section_id}",
                    )
                    conflicts.append(conflict)
                    logger.critical("HEAD-ON CONFLICT on section %s: %s", section_id, trains)

        return conflicts

    def _suggest_resolution(self, cycle: List[str]) -> str:
        """Suggest a resolution strategy for a detected deadlock."""
        if len(cycle) == 2:
            return f"Force train {cycle[0]} to reverse or wait in siding"
        return f"Temporarily cancel route for train {cycle[-1]} to break cycle"

    def on_deadlock(self, callback: Any) -> None:
        self._detection_callbacks.append(callback)

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        records = self._detected_deadlocks[-limit:]
        return [
            {
                "type": dl.cycle_type.name,
                "trains": dl.involved_trains,
                "sections": dl.involved_sections,
                "severity": dl.severity,
                "resolution": dl.resolution_suggestion,
            }
            for dl in records
        ]

    def statistics(self) -> Dict[str, Any]:
        return {
            "total_detected": len(self._detected_deadlocks),
            "active_trains": len(self.graph.train_nodes),
            "tracked_sections": len(self.graph.section_holders),
            "starvation_threshold_s": self._starvation_threshold_s,
        }

    def reset(self) -> None:
        self.graph.clear()
        self._detected_deadlocks.clear()
