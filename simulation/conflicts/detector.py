"""Railway Traffic Conflict Detection Engine."""
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional
from simulation.trains.train import SimulationTrain
from simulation.network.elements import TrackEdge
from simulation.network.graph import RailwayNetwork
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class ConflictRecord:
    def __init__(
        self,
        conflict_type: str,
        severity: str,
        location_type: str,
        location_id: str,
        primary_train_id: str,
        secondary_train_id: Optional[str],
        cause: str,
        predicted_impact: str,
        recommendation: str,
        affected_resources: List[str],
        detected_at: datetime
    ):
        self.id = f"CONF_{uuid.uuid4().hex[:8].upper()}"
        self.conflict_type = conflict_type
        self.severity = severity
        self.status = "ACTIVE"
        self.location_type = location_type
        self.location_id = location_id
        self.primary_train_id = primary_train_id
        self.secondary_train_id = secondary_train_id
        self.cause = cause
        self.predicted_impact = predicted_impact
        self.recommendation = recommendation
        self.affected_resources = affected_resources
        self.detected_at = detected_at
        self.resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "status": self.status,
            "location_type": self.location_type,
            "location_id": self.location_id,
            "primary_train_id": self.primary_train_id,
            "secondary_train_id": self.secondary_train_id,
            "cause": self.cause,
            "predicted_impact": self.predicted_impact,
            "recommendation": self.recommendation,
            "affected_resources": self.affected_resources,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class ConflictDetector:
    """Detects spatial-temporal, headway, junction, and platform conflicts."""
    
    MIN_HEADWAY_SECONDS = 180.0  # 3 minutes standard safe headway
    MIN_HEADWAY_DISTANCE_KM = 2.0  # 2 km safe following distance

    def __init__(self, network: RailwayNetwork):
        self.network = network
        self.active_conflicts: Dict[str, ConflictRecord] = {}
        self.resolved_conflicts: List[ConflictRecord] = []

    def scan_conflicts(self, active_trains: List[SimulationTrain], sim_time: datetime) -> List[ConflictRecord]:
        """Scan active trains and network resources for conflicts."""
        newly_detected = []
        train_map = {t.id: t for t in active_trains}
        
        # 1. Same-Track & Headway Conflicts
        for track_id, track in self.network.tracks.items():
            occupying_train_ids = [tid for tid in track.current_train_ids if tid in train_map]
            
            # If 2 or more trains on same track
            if len(occupying_train_ids) >= 2:
                t1 = train_map[occupying_train_ids[0]]
                t2 = train_map[occupying_train_ids[1]]
                
                # Check spatial separation
                dist_diff = abs(t1.distance_along_current_track_km - t2.distance_along_current_track_km)
                
                # Opposite directions on single track = CRITICAL HEAD-ON COLLISION RISK
                if (t1.route_tracks and t2.route_tracks and 
                    t1.current_track and t2.current_track and
                    t1.current_track.source_node == t2.current_track.target_node):
                    
                    conflict_key = f"HEADON_{track_id}_{t1.id}_{t2.id}"
                    if conflict_key not in self.active_conflicts:
                        conf = ConflictRecord(
                            conflict_type="SAME_TRACK_OPPOSITE_DIRECTION",
                            severity="CRITICAL",
                            location_type="TRACK",
                            location_id=track_id,
                            primary_train_id=t1.id,
                            secondary_train_id=t2.id,
                            cause=f"Trains {t1.train_number} and {t2.train_number} travelling in opposing directions on track {track.name}",
                            predicted_impact="Imminent deadlock and emergency braking required; network gridlock risk.",
                            recommendation=f"Emergency hold train {t2.train_number} at preceding siding or switch.",
                            affected_resources=[track_id, track.source_node, track.target_node],
                            detected_at=sim_time
                        )
                        self.active_conflicts[conflict_key] = conf
                        newly_detected.append(conf)
                        self._emit_event(conf, sim_time)

                elif dist_diff < self.MIN_HEADWAY_DISTANCE_KM:
                    conflict_key = f"HEADWAY_{track_id}_{t1.id}_{t2.id}"
                    if conflict_key not in self.active_conflicts:
                        lead = t1 if t1.distance_along_current_track_km > t2.distance_along_current_track_km else t2
                        trail = t2 if lead == t1 else t1
                        conf = ConflictRecord(
                            conflict_type="HEADWAY_VIOLATION",
                            severity="HIGH",
                            location_type="TRACK",
                            location_id=track_id,
                            primary_train_id=trail.id,
                            secondary_train_id=lead.id,
                            cause=f"Trailing train {trail.train_number} is within {dist_diff:.2f} km of lead train {lead.train_number} (min safe: {self.MIN_HEADWAY_DISTANCE_KM} km)",
                            predicted_impact=f"Trailing train {trail.train_number} will encounter yellow/red signals, causing cascade delays.",
                            recommendation=f"Reduce target speed of train {trail.train_number} to 60 km/h to restore 3-minute headway buffer.",
                            affected_resources=[track_id],
                            detected_at=sim_time
                        )
                        self.active_conflicts[conflict_key] = conf
                        newly_detected.append(conf)
                        self._emit_event(conf, sim_time)

        # 2. Junction Contention Conflicts
        # Trains converging on the same junction within close arrival times
        junction_arrivals: Dict[str, List[SimulationTrain]] = {}
        for train in active_trains:
            if train.status in ("RUNNING", "SCHEDULED") and train.current_track:
                target_node = train.current_track.target_node
                if target_node in self.network.junctions:
                    if target_node not in junction_arrivals:
                        junction_arrivals[target_node] = []
                    junction_arrivals[target_node].append(train)

        for jct_id, approaching_trains in junction_arrivals.items():
            if len(approaching_trains) >= 2:
                t1, t2 = approaching_trains[0], approaching_trains[1]
                t1_dist = max(0.1, t1.current_track.length_km - t1.distance_along_current_track_km)
                t2_dist = max(0.1, t2.current_track.length_km - t2.distance_along_current_track_km)
                
                t1_eta_min = (t1_dist / max(20.0, t1.current_speed_kmh)) * 60.0
                t2_eta_min = (t2_dist / max(20.0, t2.current_speed_kmh)) * 60.0

                if abs(t1_eta_min - t2_eta_min) < 3.0:  # within 3 minutes of simultaneous arrival
                    conflict_key = f"JCT_{jct_id}_{t1.id}_{t2.id}"
                    if conflict_key not in self.active_conflicts:
                        # Prioritize higher priority train
                        lower_prio = t2 if t1.priority >= t2.priority else t1
                        higher_prio = t1 if lower_prio == t2 else t2
                        conf = ConflictRecord(
                            conflict_type="JUNCTION_CONTENTION",
                            severity="HIGH",
                            location_type="JUNCTION",
                            location_id=jct_id,
                            primary_train_id=lower_prio.id,
                            secondary_train_id=higher_prio.id,
                            cause=f"Simultaneous convergence at junction {jct_id} by {t1.train_number} and {t2.train_number}",
                            predicted_impact=f"Potential deadlock at junction switches; delay propagation to both corridors.",
                            recommendation=f"Grant signal priority to train {higher_prio.train_number} (priority {higher_prio.priority}); hold train {lower_prio.train_number} at approach signal.",
                            affected_resources=[jct_id],
                            detected_at=sim_time
                        )
                        self.active_conflicts[conflict_key] = conf
                        newly_detected.append(conf)
                        self._emit_event(conf, sim_time)

        # 3. Clean up resolved conflicts
        resolved_keys = []
        for key, conf in list(self.active_conflicts.items()):
            # If trains involved are completed or separated
            p_train = train_map.get(conf.primary_train_id)
            s_train = train_map.get(conf.secondary_train_id) if conf.secondary_train_id else None
            
            is_resolved = False
            if not p_train or p_train.status == "COMPLETED":
                is_resolved = True
            elif s_train and s_train.status == "COMPLETED":
                is_resolved = True
            elif conf.conflict_type == "HEADWAY_VIOLATION" and p_train and s_train:
                if p_train.current_track != s_train.current_track:
                    is_resolved = True
                    
            if is_resolved:
                conf.status = "RESOLVED"
                conf.resolved_at = sim_time
                self.resolved_conflicts.append(conf)
                resolved_keys.append(key)
                event_bus.publish(SimEvent(
                    event_type=EventType.CONFLICT_RESOLVED,
                    sim_time=sim_time,
                    entity_id=conf.id,
                    entity_type="CONFLICT",
                    payload={"conflict_id": conf.id, "type": conf.conflict_type}
                ))

        for k in resolved_keys:
            del self.active_conflicts[k]

        return newly_detected

    def _emit_event(self, conf: ConflictRecord, sim_time: datetime):
        event_bus.publish(SimEvent(
            event_type=EventType.CONFLICT_DETECTED,
            sim_time=sim_time,
            entity_id=conf.id,
            entity_type="CONFLICT",
            payload=conf.to_dict()
        ))

    def resolve_conflict(self, conflict_id: str, strategy: str, sim_time: datetime) -> bool:
        """Manually or autonomously resolve a conflict with an applied strategy."""
        for key, conf in list(self.active_conflicts.items()):
            if conf.id == conflict_id:
                conf.status = "RESOLVED"
                conf.resolved_at = sim_time
                self.resolved_conflicts.append(conf)
                del self.active_conflicts[key]
                event_bus.publish(SimEvent(
                    event_type=EventType.CONFLICT_RESOLVED,
                    sim_time=sim_time,
                    entity_id=conf.id,
                    entity_type="CONFLICT",
                    payload={"conflict_id": conf.id, "strategy": strategy}
                ))
                return True
        return False
