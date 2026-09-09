"""
Interlocking Table for Computer-Based Interlocking.

The interlocking table is the core data structure encoding:
- All valid routes and their required point/signal settings
- Conflicting route matrix
- Approach locking conditions
- Overlap requirements
- Flank protection requirements

Based on EN 50128/50129 SIL-4 interlocking table standards.
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TableEntry:
    """A single row in the interlocking table."""
    route_id: str
    entry_signal: str
    exit_signal: str

    # Required point positions: {point_id: position}
    point_requirements: Dict[str, str] = field(default_factory=dict)

    # Required track sections (must be clear)
    sections_required: List[str] = field(default_factory=list)

    # Overlap requirement
    overlap_id: Optional[str] = None

    # Flank protection
    flank_elements: List[str] = field(default_factory=list)

    # Conflicting routes (cannot be simultaneously set)
    conflicts: Set[str] = field(default_factory=set)

    # Speed restriction
    max_speed_kmh: float = 160.0

    # Priority (for arbitration when multiple routes requested)
    priority: int = 0

    # Category
    category: str = "MAIN"   # MAIN, SHUNT, CALLING_ON, EMERGENCY

    # Notes (for documentation/audit)
    notes: str = ""

    def __repr__(self) -> str:
        return (f"TableEntry({self.route_id!r}: "
                f"{self.entry_signal!r} -> {self.exit_signal!r})")


@dataclass
class ConflictMatrix:
    """Symmetric matrix encoding route conflicts."""
    route_ids: List[str] = field(default_factory=list)
    _matrix: Dict[FrozenSet[str], bool] = field(default_factory=dict)

    def set_conflict(self, route_a: str, route_b: str) -> None:
        key = frozenset([route_a, route_b])
        self._matrix[key] = True

    def is_conflict(self, route_a: str, route_b: str) -> bool:
        key = frozenset([route_a, route_b])
        return self._matrix.get(key, False)

    def get_all_conflicts(self, route_id: str) -> List[str]:
        return [
            other
            for key in self._matrix
            if route_id in key and self._matrix[key]
            for other in key
            if other != route_id
        ]

    def conflict_count(self) -> int:
        return sum(1 for v in self._matrix.values() if v)

    def to_dict(self) -> Dict[str, List[str]]:
        result: Dict[str, List[str]] = {}
        for route_id in self.route_ids:
            result[route_id] = self.get_all_conflicts(route_id)
        return result


class InterlockingTable:
    """
    Master interlocking table managing all routes and their conditions.
    Provides lookup, validation, and export capabilities.
    """

    def __init__(self, name: str = "CBI_TABLE") -> None:
        self.name = name
        self.entries: Dict[str, TableEntry] = {}
        self.conflict_matrix = ConflictMatrix()
        self._signal_to_routes: Dict[str, List[str]] = {}   # entry_signal -> route_ids
        self._section_to_routes: Dict[str, List[str]] = {}  # section -> route_ids

    def add_entry(self, entry: TableEntry) -> None:
        self.entries[entry.route_id] = entry

        # Update conflict matrix
        if entry.route_id not in self.conflict_matrix.route_ids:
            self.conflict_matrix.route_ids.append(entry.route_id)

        for conflict_id in entry.conflicts:
            self.conflict_matrix.set_conflict(entry.route_id, conflict_id)

        # Update signal index
        if entry.entry_signal not in self._signal_to_routes:
            self._signal_to_routes[entry.entry_signal] = []
        self._signal_to_routes[entry.entry_signal].append(entry.route_id)

        # Update section index
        for section in entry.sections_required:
            if section not in self._section_to_routes:
                self._section_to_routes[section] = []
            self._section_to_routes[section].append(entry.route_id)

    def get_entry(self, route_id: str) -> Optional[TableEntry]:
        return self.entries.get(route_id)

    def get_routes_from_signal(self, signal_id: str) -> List[TableEntry]:
        route_ids = self._signal_to_routes.get(signal_id, [])
        return [self.entries[rid] for rid in route_ids if rid in self.entries]

    def get_conflicting_routes(self, route_id: str) -> List[str]:
        return self.conflict_matrix.get_all_conflicts(route_id)

    def validate_table(self) -> List[str]:
        """
        Validate the interlocking table for consistency.
        Returns list of validation errors.
        """
        errors = []

        for route_id, entry in self.entries.items():
            # Check conflict symmetry
            for conflict_id in entry.conflicts:
                if conflict_id in self.entries:
                    other_entry = self.entries[conflict_id]
                    if route_id not in other_entry.conflicts:
                        errors.append(
                            f"Asymmetric conflict: {route_id!r} conflicts with {conflict_id!r} "
                            f"but not vice versa"
                        )

            # Check self-conflict
            if route_id in entry.conflicts:
                errors.append(f"Route {route_id!r} conflicts with itself")

            # Check entry/exit signal exist
            if not entry.entry_signal:
                errors.append(f"Route {route_id!r} has no entry signal")
            if not entry.exit_signal:
                errors.append(f"Route {route_id!r} has no exit signal")

            # Check at least one section
            if not entry.sections_required:
                errors.append(f"Route {route_id!r} has no sections defined")

        return errors

    def auto_compute_conflicts(self) -> int:
        """
        Automatically compute route conflicts based on shared sections.
        Returns number of conflict pairs found.
        """
        count = 0
        route_list = list(self.entries.values())
        for i, entry_a in enumerate(route_list):
            for j, entry_b in enumerate(route_list):
                if i >= j:
                    continue
                shared = set(entry_a.sections_required) & set(entry_b.sections_required)
                if shared:
                    entry_a.conflicts.add(entry_b.route_id)
                    entry_b.conflicts.add(entry_a.route_id)
                    self.conflict_matrix.set_conflict(entry_a.route_id, entry_b.route_id)
                    count += 1
        return count

    def to_json(self) -> str:
        """Export interlocking table to JSON."""
        data = {
            "name": self.name,
            "routes": [
                {
                    "route_id": e.route_id,
                    "entry_signal": e.entry_signal,
                    "exit_signal": e.exit_signal,
                    "point_requirements": e.point_requirements,
                    "sections_required": e.sections_required,
                    "overlap_id": e.overlap_id,
                    "flank_elements": e.flank_elements,
                    "conflicts": list(e.conflicts),
                    "max_speed_kmh": e.max_speed_kmh,
                    "priority": e.priority,
                    "category": e.category,
                    "notes": e.notes,
                }
                for e in self.entries.values()
            ],
            "total_routes": len(self.entries),
            "total_conflicts": self.conflict_matrix.conflict_count(),
        }
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "InterlockingTable":
        """Load interlocking table from JSON."""
        data = json.loads(json_str)
        table = cls(name=data.get("name", "CBI_TABLE"))
        for route_data in data.get("routes", []):
            entry = TableEntry(
                route_id=route_data["route_id"],
                entry_signal=route_data["entry_signal"],
                exit_signal=route_data["exit_signal"],
                point_requirements=route_data.get("point_requirements", {}),
                sections_required=route_data.get("sections_required", []),
                overlap_id=route_data.get("overlap_id"),
                flank_elements=route_data.get("flank_elements", []),
                conflicts=set(route_data.get("conflicts", [])),
                max_speed_kmh=route_data.get("max_speed_kmh", 160.0),
                priority=route_data.get("priority", 0),
                category=route_data.get("category", "MAIN"),
                notes=route_data.get("notes", ""),
            )
            table.add_entry(entry)
        return table

    def to_csv(self) -> str:
        """Export interlocking table to CSV format."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "route_id", "entry_signal", "exit_signal",
            "sections", "points", "overlap", "conflicts",
            "max_speed_kmh", "category"
        ])
        for entry in self.entries.values():
            writer.writerow([
                entry.route_id,
                entry.entry_signal,
                entry.exit_signal,
                "|".join(entry.sections_required),
                json.dumps(entry.point_requirements),
                entry.overlap_id or "",
                "|".join(entry.conflicts),
                entry.max_speed_kmh,
                entry.category,
            ])
        return output.getvalue()

    def statistics(self) -> Dict[str, Any]:
        categories = {}
        for entry in self.entries.values():
            categories[entry.category] = categories.get(entry.category, 0) + 1

        return {
            "table_name": self.name,
            "total_routes": len(self.entries),
            "total_conflicts": self.conflict_matrix.conflict_count(),
            "categories": categories,
            "total_sections_referenced": len(self._section_to_routes),
            "total_signals_referenced": len(self._signal_to_routes),
        }
