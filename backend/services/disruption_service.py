"""Disruption and Dynamic Delay Management Service."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.models.conflict import Disruption, DelayEvent
from backend.repositories.disruption_repository import DisruptionRepository, DelayEventRepository
from backend.repositories.train_repository import TrainRepository
from backend.repositories.network_repository import TrackRepository
from simulation.engine.simulator import sim_engine

class DisruptionService:
    """Orchestrates live disruption injection, impact analysis, and cascading delay logging."""

    @classmethod
    def register_disruption(
        cls,
        disruption_id: str,
        disruption_type: str,
        affected_resource_type: str,
        affected_resource_id: str,
        severity: str = "HIGH",
        description: Optional[str] = None,
        duration_minutes: int = 60,
        db: Optional[Session] = None
    ) -> Disruption:
        """Register disruption, perform impact analysis, apply to live simulation and persist."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            dis_repo = DisruptionRepository(db)
            delay_repo = DelayEventRepository(db)
            train_repo = TrainRepository(db)
            track_repo = TrackRepository(db)

            now = datetime.now(timezone.utc)
            est_end = now + timedelta(minutes=duration_minutes)

            # 1. Identify affected trains and impact
            affected_train_ids = []
            with sim_engine.step_lock:
                for t_id, train in sim_engine.trains.items():
                    if affected_resource_type.upper() == "TRACK":
                        # Check if train is on track or has track in route
                        if train.current_track and train.current_track.id == affected_resource_id:
                            affected_train_ids.append(t_id)
                        elif any(trk.id == affected_resource_id for trk in train.route_tracks):
                            affected_train_ids.append(t_id)
                    elif affected_resource_type.upper() == "STATION":
                        if any(s.station_id == affected_resource_id for s in train.schedules):
                            affected_train_ids.append(t_id)

            impact = {
                "affected_trains_count": len(affected_train_ids),
                "affected_train_ids": affected_train_ids,
                "projected_delay_minutes": duration_minutes * (1.5 if severity.upper() == "CRITICAL" else 1.0)
            }

            # 2. Persist disruption
            disruption = Disruption(
                id=disruption_id,
                disruption_type=disruption_type.upper(),
                severity=severity.upper(),
                status="ACTIVE",
                affected_resource_type=affected_resource_type.upper(),
                affected_resource_id=affected_resource_id,
                description=description,
                start_time=now,
                estimated_end_time=est_end,
                impact_summary=impact
            )
            created = dis_repo.create(disruption)

            # 3. Apply operational blocks to simulation
            if affected_resource_type.upper() == "TRACK":
                track_repo.set_track_status(affected_resource_id, "BLOCKED", reason=description)
                with sim_engine.step_lock:
                    if affected_resource_id in sim_engine.network.tracks:
                        sim_engine.network.tracks[affected_resource_id].status = "BLOCKED"

            # 4. Inject delay events for directly affected trains
            for t_id in affected_train_ids:
                delay_repo.log_delay(
                    train_id=t_id,
                    delay_minutes=float(duration_minutes),
                    delay_type="PRIMARY",
                    cause=f"Direct impact from disruption: {disruption_id} ({disruption_type})",
                    track_id=affected_resource_id if affected_resource_type.upper() == "TRACK" else None,
                    disruption_id=disruption_id
                )
                train_repo.record_status_transition(t_id, "DELAYED", reason=f"Disruption on {affected_resource_id}", delay_min=float(duration_minutes))
                if t_id in sim_engine.trains:
                    sim_engine.trains[t_id].current_delay_minutes += float(duration_minutes)

            return created
        finally:
            if close_db:
                db.close()

    @classmethod
    def resolve_disruption(cls, disruption_id: str, db: Optional[Session] = None) -> Optional[Disruption]:
        """Resolve disruption and restore track/infrastructure capacity."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            dis_repo = DisruptionRepository(db)
            track_repo = TrackRepository(db)

            resolved = dis_repo.resolve_disruption(disruption_id)
            if not resolved:
                return None

            # Restore simulation network resource if track
            if resolved.affected_resource_type.upper() == "TRACK":
                track_repo.set_track_status(resolved.affected_resource_id, "CLEAR")
                with sim_engine.step_lock:
                    if resolved.affected_resource_id in sim_engine.network.tracks:
                        sim_engine.network.tracks[resolved.affected_resource_id].status = "CLEAR"

            return resolved
        finally:
            if close_db:
                db.close()

    @classmethod
    def list_disruptions(cls, active_only: bool = True, db: Optional[Session] = None) -> List[Disruption]:
        """List active or historical disruptions."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = DisruptionRepository(db)
            if active_only:
                return repo.get_active_disruptions()
            return repo.list()
        finally:
            if close_db:
                db.close()

    @classmethod
    def log_delay_event(
        cls,
        train_id: str,
        delay_minutes: float,
        delay_type: str = "PRIMARY",
        cause: str = "Operational delay",
        station_id: Optional[str] = None,
        track_id: Optional[str] = None,
        disruption_id: Optional[str] = None,
        db: Optional[Session] = None
    ) -> DelayEvent:
        """Log structured delay incident and update train delay state."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = DelayEventRepository(db)
            train_repo = TrainRepository(db)

            event = repo.log_delay(
                train_id=train_id,
                delay_minutes=delay_minutes,
                delay_type=delay_type,
                cause=cause,
                station_id=station_id,
                track_id=track_id,
                disruption_id=disruption_id
            )

            train = train_repo.get(train_id)
            if train:
                train.current_delay_minutes += delay_minutes
                db.commit()

            if train_id in sim_engine.trains:
                sim_engine.trains[train_id].current_delay_minutes += delay_minutes

            return event
        finally:
            if close_db:
                db.close()

    @classmethod
    def list_delays(cls, train_id: Optional[str] = None, limit: int = 100, db: Optional[Session] = None) -> List[DelayEvent]:
        """Fetch delay history for a train or entire corridor."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = DelayEventRepository(db)
            if train_id:
                return repo.get_delays_for_train(train_id, limit=limit)
            return repo.get_recent_network_delays(limit=limit)
        finally:
            if close_db:
                db.close()
