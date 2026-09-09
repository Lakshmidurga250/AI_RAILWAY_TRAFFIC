"""Conflict Resolution Arbiter Engine."""
from typing import Dict, Any, List, Optional
from simulation.conflicts.detector import ConflictRecord
from simulation.network.graph import RailwayNetwork

class ConflictResolver:
    """Evaluates active conflicts and determines optimal mitigation strategy."""

    @classmethod
    def resolve(cls, conflict: ConflictRecord, network: RailwayNetwork) -> Dict[str, Any]:
        conflict_type = conflict.conflict_type
        strategy = "SPEED_ADJUSTMENT"
        action_params = {}
        rationale = ""

        if conflict_type == "HEADWAY_VIOLATION":
            strategy = "SPEED_ADJUSTMENT"
            action_params = {"target_train_id": conflict.primary_train_id, "speed_limit_kmh": 60.0}
            rationale = "Reduce trailing train speed to 60 km/h to re-establish 3-minute safety headway."

        elif conflict_type in ("SAME_TRACK_OPPOSITE_DIRECTION", "HEAD_ON_COLLISION_RISK"):
            strategy = "HOLD_TRAIN"
            action_params = {"hold_train_id": conflict.primary_train_id, "hold_location": conflict.location_id}
            rationale = "Immediate emergency hold command issued to primary train at nearest approach signal."

        elif conflict_type == "JUNCTION_CONTENTION":
            strategy = "SIGNAL_INTERLOCK_PRIORITY"
            action_params = {"priority_train_id": conflict.secondary_train_id, "held_train_id": conflict.primary_train_id}
            rationale = "Grant signal progression to higher priority train; hold secondary train at junction approach."

        elif conflict_type == "PLATFORM_CONTENTION":
            strategy = "PLATFORM_REASSIGN"
            action_params = {"train_id": conflict.primary_train_id, "station_id": conflict.location_id}
            rationale = "Reassign inbound service to adjacent compatible platform."

        return {
            "conflict_id": conflict.id,
            "strategy": strategy,
            "parameters": action_params,
            "rationale": rationale,
            "expected_delay_reduction_min": 6.5
        }

conflict_resolver = ConflictResolver()
