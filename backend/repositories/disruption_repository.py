"""Disruption and Delay Event Repositories."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.conflict import Disruption, DelayEvent
from backend.repositories.base import BaseRepository

class DisruptionRepository(BaseRepository[Disruption]):
    """Repository managing track closures, signal failures, and major operational disruptions."""

    def __init__(self, db: Session):
        super().__init__(Disruption, db)

    def get_active_disruptions(self) -> List[Disruption]:
        """Fetch all currently active or mitigating disruptions."""
        return self.db.query(Disruption).filter(
            Disruption.status.in_(["ACTIVE", "MITIGATING"])
        ).order_by(desc(Disruption.start_time)).all()

    def resolve_disruption(self, disruption_id: str, end_time: Optional[datetime] = None) -> Optional[Disruption]:
        """Mark a disruption as resolved with actual resolution time."""
        disruption = self.get(disruption_id)
        if not disruption:
            return None

        disruption.status = "RESOLVED"
        disruption.actual_end_time = end_time or datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(disruption)
        return disruption

class DelayEventRepository(BaseRepository[DelayEvent]):
    """Repository managing granular primary, reactionary, and cascading delay occurrences."""

    def __init__(self, db: Session):
        super().__init__(DelayEvent, db)

    def log_delay(
        self,
        train_id: str,
        delay_minutes: float,
        delay_type: str = "PRIMARY",
        cause: str = "Unspecified delay",
        station_id: Optional[str] = None,
        track_id: Optional[str] = None,
        disruption_id: Optional[str] = None
    ) -> DelayEvent:
        """Create and commit a structured delay event record."""
        entry = DelayEvent(
            train_id=train_id,
            delay_minutes=delay_minutes,
            delay_type=delay_type.upper(),
            cause=cause,
            station_id=station_id,
            track_id=track_id,
            disruption_id=disruption_id,
            recorded_at=datetime.now(timezone.utc)
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_delays_for_train(self, train_id: str, limit: int = 50) -> List[DelayEvent]:
        """Fetch chronological delay incidents for a train."""
        return self.db.query(DelayEvent).filter(
            DelayEvent.train_id == train_id
        ).order_by(desc(DelayEvent.recorded_at)).limit(limit).all()

    def get_recent_network_delays(self, limit: int = 100) -> List[DelayEvent]:
        """Fetch latest delay events across the entire network."""
        return self.db.query(DelayEvent).order_by(desc(DelayEvent.recorded_at)).limit(limit).all()
