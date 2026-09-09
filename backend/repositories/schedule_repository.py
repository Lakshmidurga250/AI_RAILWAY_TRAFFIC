"""Schedule and Timetable Version Repositories."""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.train import Schedule, ScheduleVersion, ScheduleStop
from backend.repositories.base import BaseRepository

class ScheduleVersionRepository(BaseRepository[ScheduleVersion]):
    """Repository managing published and what-if timetable revisions."""

    def __init__(self, db: Session):
        super().__init__(ScheduleVersion, db)

    def get_active_version(self) -> Optional[ScheduleVersion]:
        """Fetch currently active master timetable version."""
        return self.db.query(ScheduleVersion).filter(ScheduleVersion.is_active == True).order_by(desc(ScheduleVersion.created_at)).first()

    def create_version(self, version_code: str, name: str, description: Optional[str] = None) -> ScheduleVersion:
        """Create and publish a timetable revision."""
        v = ScheduleVersion(
            version_code=version_code,
            name=name,
            description=description,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

class ScheduleRepository(BaseRepository[Schedule]):
    """Repository managing scheduled train assignments and stops."""

    def __init__(self, db: Session):
        super().__init__(Schedule, db)

    def get_active_schedule_for_train(self, train_id: str) -> Optional[Schedule]:
        """Get active schedule instance for train."""
        return self.db.query(Schedule).filter(
            Schedule.train_id == train_id,
            Schedule.is_active == True
        ).first()

    def get_train_stops(self, train_id: str) -> List[ScheduleStop]:
        """Retrieve ordered schedule stops for train."""
        return self.db.query(ScheduleStop).filter(
            ScheduleStop.train_id == train_id
        ).order_by(ScheduleStop.stop_sequence.asc()).all()
