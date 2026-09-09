"""Train repository providing persistence, search, status history, and position tracking."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from backend.models.train import Train, TrainType, TrainCategory, TrainStatusHistory, TrainPosition
from backend.repositories.base import BaseRepository

DEFAULT_TRAIN_TYPES = [
    ("HIGH_SPEED", "High-Speed Passenger Bullet Train", 300.0, 1.2, 1.4, "Aerodynamic electric multiple unit for express intercity corridors"),
    ("INTERCITY", "Intercity Express Train", 160.0, 0.8, 1.0, "Standard locomotive-hauled or EMU express linking metropolitan hubs"),
    ("REGIONAL", "Regional Suburban Train", 120.0, 0.9, 1.1, "High-density commuter train with frequent stops"),
    ("COMMUTER", "Commuter Metro Rail", 90.0, 1.1, 1.2, "Rapid transit metro train serving urban inner corridors"),
    ("FREIGHT", "Heavy-Haul Freight Train", 80.0, 0.3, 0.5, "Long consist bulk goods and intermodal freight transport"),
]

DEFAULT_CATEGORIES = [
    ("PASSENGER_PRIORITY", "High-Priority Passenger Express", 9, True),
    ("PASSENGER_STANDARD", "Standard Timetabled Passenger", 6, True),
    ("FREIGHT_BULK", "Heavy Freight (Minerals & Cargo)", 3, False),
    ("MAINTENANCE_SPECIAL", "Track Inspection & Maintenance Vehicle", 10, False),
]

class TrainRepository(BaseRepository[Train]):
    """Repository managing Train entity lifecycle, status transitions, and spatial telemetry."""

    def __init__(self, db: Session):
        super().__init__(Train, db)

    def get_by_number(self, train_number: str) -> Optional[Train]:
        """Fetch train by operational number."""
        return self.db.query(Train).filter(Train.train_number == train_number).first()

    def search_trains(
        self,
        status: Optional[str] = None,
        train_type: Optional[str] = None,
        priority: Optional[int] = None,
        search_query: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Train]:
        """Search and filter train records across multiple attributes."""
        query = self.db.query(Train)

        if status:
            query = query.filter(Train.status == status.upper())
        if train_type:
            query = query.filter(Train.train_type == train_type.upper())
        if priority is not None:
            query = query.filter(Train.priority == priority)
        if search_query:
            term = f"%{search_query}%"
            query = query.filter(
                or_(
                    Train.train_number.ilike(term),
                    Train.name.ilike(term),
                    Train.id.ilike(term)
                )
            )

        return query.order_by(Train.priority.desc(), Train.train_number.asc()).offset(skip).limit(limit).all()

    def record_status_transition(
        self,
        train_id: str,
        new_status: str,
        reason: Optional[str] = None,
        delay_min: float = 0.0
    ) -> Optional[TrainStatusHistory]:
        """Record status transition and update current status on Train."""
        train = self.get(train_id)
        if not train:
            return None

        previous_status = train.status
        train.status = new_status.upper()
        train.current_delay_minutes = delay_min

        history_entry = TrainStatusHistory(
            train_id=train_id,
            previous_status=previous_status,
            new_status=new_status.upper(),
            reason=reason,
            delay_at_time_min=delay_min,
            changed_at=datetime.now(timezone.utc)
        )
        self.db.add(history_entry)
        self.db.commit()
        self.db.refresh(history_entry)
        return history_entry

    def record_position(
        self,
        train_id: str,
        track_id: Optional[str],
        distance_km: float,
        latitude: float,
        longitude: float,
        speed_kmh: float
    ) -> Optional[TrainPosition]:
        """Record spatial telemetry snapshot."""
        train = self.get(train_id)
        if not train:
            return None

        # Update train current position & speed
        train.current_track_id = track_id
        train.current_lat = latitude
        train.current_lng = longitude
        train.current_speed_kmh = speed_kmh

        position = TrainPosition(
            train_id=train_id,
            track_id=track_id,
            distance_along_track_km=distance_km,
            latitude=latitude,
            longitude=longitude,
            speed_kmh=speed_kmh,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def get_status_history(self, train_id: str, limit: int = 50) -> List[TrainStatusHistory]:
        """Fetch chronologically descending status history."""
        return self.db.query(TrainStatusHistory).filter(
            TrainStatusHistory.train_id == train_id
        ).order_by(desc(TrainStatusHistory.changed_at)).limit(limit).all()

    def get_positions_trail(self, train_id: str, limit: int = 100) -> List[TrainPosition]:
        """Fetch recent spatial position breadcrumbs for track visualization."""
        return self.db.query(TrainPosition).filter(
            TrainPosition.train_id == train_id
        ).order_by(desc(TrainPosition.timestamp)).limit(limit).all()

    def seed_types_and_categories(self):
        """Seed default train types and train categories if absent."""
        for code, name, max_spd, acc, brk, desc_txt in DEFAULT_TRAIN_TYPES:
            existing = self.db.query(TrainType).filter(TrainType.code == code).first()
            if not existing:
                tt = TrainType(
                    code=code,
                    name=name,
                    description=desc_txt,
                    default_max_speed_kmh=max_spd,
                    default_acceleration_ms2=acc,
                    default_braking_ms2=brk
                )
                self.db.add(tt)

        for code, name, priority, is_pass in DEFAULT_CATEGORIES:
            existing_c = self.db.query(TrainCategory).filter(TrainCategory.code == code).first()
            if not existing_c:
                tc = TrainCategory(
                    code=code,
                    name=name,
                    default_priority=priority,
                    is_passenger=is_pass
                )
                self.db.add(tc)

        self.db.commit()
