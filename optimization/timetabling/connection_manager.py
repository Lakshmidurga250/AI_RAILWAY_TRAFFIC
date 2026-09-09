"""
Connection Manager for Railway Timetabling.

Manages timed connections (Anschlüsse) between trains:
- Connection graph construction
- Transfer time validation (minimum transfer time)
- Connection weight computation (passenger volume)
- Connection symmetry (both directions)
- Conditional connections (conditional on delay)
- Connection-optimizing timetable adjustment
- Transfer penalty computation
- Cross-platform connections
- Missed connection handling and recovery
- Connection index computation
- Integrated Clock (Taktfahrplan) connections
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import time, datetime, timedelta

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    PLANNED = auto()         # Planned in timetable
    GUARANTEED = auto()      # Operator guarantees this connection
    CONDITIONAL = auto()     # Only if arriving train is on time
    BROKEN = auto()          # Connection cannot be made (missed)
    COMPLETED = auto()       # Connection successfully made
    WAIVED = auto()          # Connection waived by operator


class ConnectionType(Enum):
    SAME_PLATFORM = auto()   # Same platform cross-platform transfer
    CROSS_PLATFORM = auto()  # Different platforms
    INTERCHANGE = auto()     # Different station/hub
    BUS_RAIL = auto()        # Rail to bus connection
    INTER_MODAL = auto()     # Multi-modal connection


@dataclass
class Connection:
    """
    A timed connection between two trains at a station.
    """
    connection_id: str
    station_id: str
    station_name: str

    # Arriving train
    arriving_train_id: str
    arriving_platform: Optional[str] = None
    arrival_time: Optional[time] = None

    # Departing train
    departing_train_id: str
    departing_platform: Optional[str] = None
    departure_time: Optional[time] = None

    # Transfer properties
    connection_type: ConnectionType = ConnectionType.CROSS_PLATFORM
    minimum_transfer_time_s: int = 120     # 2 minutes default
    actual_transfer_time_s: Optional[int] = None
    walking_time_s: int = 60
    step_free_accessible: bool = True

    # Business properties
    state: ConnectionState = ConnectionState.PLANNED
    passenger_volume_daily: int = 0       # Estimated daily passengers using this connection
    commercial_importance: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL
    is_symmetric: bool = False            # Has return connection

    # Wait policy
    max_wait_time_s: int = 180            # Maximum time departing train waits
    wait_if_delay_s: int = 120            # Wait if arriving train is delayed up to this much

    def transfer_margin_s(self) -> int:
        """Time margin above minimum transfer time."""
        if self.arrival_time is None or self.departure_time is None:
            return 0
        arr_min = self.arrival_time.hour * 3600 + self.arrival_time.minute * 60 + self.arrival_time.second
        dep_min = self.departure_time.hour * 3600 + self.departure_time.minute * 60 + self.departure_time.second
        available = dep_min - arr_min
        if available < 0:
            available += 86400  # Overnight
        return available - self.minimum_transfer_time_s

    def is_tight(self) -> bool:
        return self.transfer_margin_s() < 60  # Less than 1 minute margin

    def is_feasible(self) -> bool:
        return self.transfer_margin_s() >= 0

    def would_break_if_delayed(self, delay_s: int) -> bool:
        return self.transfer_margin_s() < delay_s

    def __repr__(self) -> str:
        return (f"Connection({self.connection_id!r}, "
                f"{self.arriving_train_id!r} -> {self.departing_train_id!r}, "
                f"@{self.station_id!r}, state={self.state.name})")


@dataclass
class ConnectionBreakEvent:
    """Record of a connection break (missed connection)."""
    connection_id: str
    arriving_delay_s: int
    passengers_affected: int
    timestamp: datetime
    cause: str = ""
    recovery_action: str = ""


@dataclass
class TransferIndex:
    """UIC connectivity index for a station or network."""
    station_id: str
    total_connections: int
    guaranteed_connections: int
    feasible_connections: int
    tight_connections: int  # < 60s margin
    average_transfer_margin_s: float
    connection_reliability: float  # 0-1 (ratio feasible/total)
    connectivity_score: float      # Composite score 0-100


class ConnectionManager:
    """
    Manages the complete connection graph for a railway timetable.
    Implements the Integrated Clock (Taktfahrplan) connection optimization.
    """

    def __init__(self, min_transfer_time_s: int = 120) -> None:
        self.min_transfer_time_s = min_transfer_time_s
        self.connections: Dict[str, Connection] = {}
        self._station_connections: Dict[str, List[str]] = {}  # station -> [connection_ids]
        self._train_connections: Dict[str, List[str]] = {}   # train -> [connection_ids]
        self._break_events: List[ConnectionBreakEvent] = []

    def register_connection(self, connection: Connection) -> None:
        self.connections[connection.connection_id] = connection

        # Update station index
        sid = connection.station_id
        if sid not in self._station_connections:
            self._station_connections[sid] = []
        self._station_connections[sid].append(connection.connection_id)

        # Update train indices
        for train_id in [connection.arriving_train_id, connection.departing_train_id]:
            if train_id not in self._train_connections:
                self._train_connections[train_id] = []
            self._train_connections[train_id].append(connection.connection_id)

    def get_connections_at_station(self, station_id: str) -> List[Connection]:
        conn_ids = self._station_connections.get(station_id, [])
        return [self.connections[cid] for cid in conn_ids if cid in self.connections]

    def get_train_connections(self, train_id: str) -> List[Connection]:
        conn_ids = self._train_connections.get(train_id, [])
        return [self.connections[cid] for cid in conn_ids if cid in self.connections]

    def auto_detect_connections(self, train_stops: Dict[str, List[Dict[str, Any]]],
                                  max_transfer_window_s: int = 600) -> int:
        """
        Automatically detect potential connections by finding trains
        with overlapping station stops within the transfer window.
        Returns number of connections created.
        """
        count = 0
        station_arrivals: Dict[str, List[Dict[str, Any]]] = {}

        for train_id, stops in train_stops.items():
            for stop in stops:
                station = stop.get("station_id", "")
                arr_s = stop.get("arrival_s", 0)
                dep_s = stop.get("departure_s", 0)

                if station not in station_arrivals:
                    station_arrivals[station] = []
                station_arrivals[station].append({
                    "train_id": train_id,
                    "arrival_s": arr_s,
                    "departure_s": dep_s,
                    "platform": stop.get("platform"),
                })

        for station_id, events in station_arrivals.items():
            # Sort by arrival time
            events_sorted = sorted(events, key=lambda e: e["arrival_s"])

            for i, arriving in enumerate(events_sorted):
                for departing in events_sorted[i + 1:]:
                    if departing["train_id"] == arriving["train_id"]:
                        continue
                    transfer_window = departing["departure_s"] - arriving["arrival_s"]
                    if self.min_transfer_time_s <= transfer_window <= max_transfer_window_s:
                        conn_id = (f"AUTO_{arriving['train_id']}_"
                                   f"{departing['train_id']}_{station_id}")
                        conn = Connection(
                            connection_id=conn_id,
                            station_id=station_id,
                            station_name=station_id,
                            arriving_train_id=arriving["train_id"],
                            arriving_platform=arriving.get("platform"),
                            departing_train_id=departing["train_id"],
                            departing_platform=departing.get("platform"),
                            minimum_transfer_time_s=self.min_transfer_time_s,
                            actual_transfer_time_s=int(transfer_window),
                        )
                        self.register_connection(conn)
                        count += 1

        logger.info("Auto-detected %d connections at %d stations",
                    count, len(station_arrivals))
        return count

    def validate_all_connections(self) -> List[Dict[str, Any]]:
        """Validate all connections and return list of issues."""
        issues = []
        for conn_id, conn in self.connections.items():
            if not conn.is_feasible():
                issues.append({
                    "connection_id": conn_id,
                    "issue": "INFEASIBLE",
                    "transfer_margin_s": conn.transfer_margin_s(),
                    "min_required_s": conn.minimum_transfer_time_s,
                })
            elif conn.is_tight():
                issues.append({
                    "connection_id": conn_id,
                    "issue": "TIGHT",
                    "transfer_margin_s": conn.transfer_margin_s(),
                    "risk": "high_miss_probability",
                })
        return issues

    def simulate_delay_propagation(self, train_id: str,
                                   delay_s: int) -> List[Dict[str, Any]]:
        """
        Simulate how a delay in one train propagates through connections.
        Returns list of connections that would break.
        """
        broken = []
        visited = set()
        queue = [(train_id, delay_s)]

        while queue:
            current_train, current_delay = queue.pop(0)
            if current_train in visited:
                continue
            visited.add(current_train)

            conn_ids = self._train_connections.get(current_train, [])
            for cid in conn_ids:
                conn = self.connections.get(cid)
                if not conn or conn.arriving_train_id != current_train:
                    continue
                if conn.would_break_if_delayed(current_delay):
                    conn.state = ConnectionState.BROKEN
                    missed_passengers = conn.passenger_volume_daily
                    broken.append({
                        "connection_id": cid,
                        "station": conn.station_id,
                        "departing_train": conn.departing_train_id,
                        "delay_needed_s": conn.transfer_margin_s(),
                        "delay_actual_s": current_delay,
                        "passengers_affected": missed_passengers,
                    })
                    # Propagate partial delay to departing train
                    propagated_delay = max(0, current_delay - conn.transfer_margin_s())
                    if propagated_delay > 0:
                        queue.append((conn.departing_train_id, propagated_delay))

        return broken

    def record_break(self, connection_id: str, arriving_delay_s: int,
                     passengers_affected: int = 0, cause: str = "") -> None:
        event = ConnectionBreakEvent(
            connection_id=connection_id,
            arriving_delay_s=arriving_delay_s,
            passengers_affected=passengers_affected,
            timestamp=datetime.utcnow(),
            cause=cause,
        )
        self._break_events.append(event)
        if connection_id in self.connections:
            self.connections[connection_id].state = ConnectionState.BROKEN
        logger.warning("Connection %s broken — %d passengers affected", connection_id, passengers_affected)

    def compute_transfer_index(self, station_id: str) -> TransferIndex:
        """Compute connectivity index for a station."""
        conns = self.get_connections_at_station(station_id)
        if not conns:
            return TransferIndex(station_id, 0, 0, 0, 0, 0, 0, 0)

        feasible = sum(1 for c in conns if c.is_feasible())
        tight = sum(1 for c in conns if c.is_tight())
        guaranteed = sum(1 for c in conns if c.state == ConnectionState.GUARANTEED)
        margins = [c.transfer_margin_s() for c in conns]
        avg_margin = sum(margins) / len(margins) if margins else 0
        reliability = feasible / len(conns) if conns else 0

        # Composite score
        score = (reliability * 40 + min(avg_margin / 300, 1) * 30 +
                 guaranteed / len(conns) * 30 if conns else 0)

        return TransferIndex(
            station_id=station_id,
            total_connections=len(conns),
            guaranteed_connections=guaranteed,
            feasible_connections=feasible,
            tight_connections=tight,
            average_transfer_margin_s=avg_margin,
            connection_reliability=reliability,
            connectivity_score=score,
        )

    def network_connectivity_report(self) -> Dict[str, Any]:
        """Generate network-wide connection analysis."""
        all_stations = list(self._station_connections.keys())
        indices = [self.compute_transfer_index(sid) for sid in all_stations]

        return {
            "total_connections": len(self.connections),
            "total_stations": len(all_stations),
            "feasible_connections": sum(1 for c in self.connections.values() if c.is_feasible()),
            "broken_connections": sum(1 for c in self.connections.values()
                                      if c.state == ConnectionState.BROKEN),
            "total_break_events": len(self._break_events),
            "average_connectivity_score": sum(i.connectivity_score for i in indices) / len(indices) if indices else 0,
            "worst_stations": sorted(
                [{"station_id": i.station_id, "score": round(i.connectivity_score, 1)}
                 for i in indices],
                key=lambda x: x["score"]
            )[:5],
            "best_stations": sorted(
                [{"station_id": i.station_id, "score": round(i.connectivity_score, 1)}
                 for i in indices],
                key=lambda x: x["score"],
                reverse=True
            )[:5],
        }

    def statistics(self) -> Dict[str, Any]:
        states: Dict[str, int] = {}
        for state in ConnectionState:
            states[state.name] = sum(1 for c in self.connections.values() if c.state == state)
        return {
            "total_connections": len(self.connections),
            "state_distribution": states,
            "total_break_events": len(self._break_events),
            "stations_with_connections": len(self._station_connections),
        }
