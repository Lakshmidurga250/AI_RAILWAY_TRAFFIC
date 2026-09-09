"""Network repositories managing Stations, Platforms, Tracks, and Corridors."""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.network import Station, Platform, Track, Junction, Switch, Signal, StationZone, Route, RouteSegment
from backend.repositories.base import BaseRepository

class StationRepository(BaseRepository[Station]):
    """Station infrastructure repository."""

    def __init__(self, db: Session):
        super().__init__(Station, db)

    def get_by_code(self, code: str) -> Optional[Station]:
        """Lookup station by station code."""
        return self.db.query(Station).filter(Station.code == code.upper()).first()

    def list_by_zone(self, zone: str) -> List[Station]:
        """Fetch all stations within a specific geographic zone."""
        return self.db.query(Station).filter(Station.zone == zone).all()

    def update_occupancy(self, station_id: str, new_occupancy: int) -> Optional[Station]:
        """Update current passenger occupancy and derive congestion status."""
        station = self.get(station_id)
        if not station:
            return None

        station.current_occupancy = max(0, new_occupancy)
        ratio = station.current_occupancy / max(1, station.passenger_capacity)
        if ratio >= 0.9:
            station.status = "CONGESTED"
        elif ratio >= 0.75:
            station.status = "RESTRICTED"
        else:
            station.status = "OPERATIONAL"

        self.db.commit()
        self.db.refresh(station)
        return station

class PlatformRepository(BaseRepository[Platform]):
    """Platform allocation and occupancy repository."""

    def __init__(self, db: Session):
        super().__init__(Platform, db)

    def get_available_platforms(self, station_id: str) -> List[Platform]:
        """Find platforms currently available for train arrival."""
        return self.db.query(Platform).filter(
            Platform.station_id == station_id,
            Platform.is_occupied == False,
            Platform.status == "AVAILABLE"
        ).all()

    def assign_train(self, platform_id: str, train_id: str) -> bool:
        """Assign platform to an arriving train."""
        p = self.get(platform_id)
        if not p or p.is_occupied:
            return False
        p.is_occupied = True
        p.current_train_id = train_id
        p.status = "OCCUPIED"
        self.db.commit()
        return True

    def release_platform(self, platform_id: str) -> bool:
        """Release platform upon train departure."""
        p = self.get(platform_id)
        if not p:
            return False
        p.is_occupied = False
        p.current_train_id = None
        p.status = "AVAILABLE"
        self.db.commit()
        return True

class TrackRepository(BaseRepository[Track]):
    """Track segment infrastructure repository."""

    def __init__(self, db: Session):
        super().__init__(Track, db)

    def set_track_status(
        self,
        track_id: str,
        status: str,
        reason: Optional[str] = None,
        speed_restriction: Optional[float] = None
    ) -> Optional[Track]:
        """Apply operational status, maintenance block, or speed restriction."""
        track = self.get(track_id)
        if not track:
            return None

        track.status = status.upper()
        track.maintenance_reason = reason
        track.speed_restriction = speed_restriction
        self.db.commit()
        self.db.refresh(track)
        return track

class RouteRepository(BaseRepository[Route]):
    """Corridor and Multi-Segment Train Route Repository."""

    def __init__(self, db: Session):
        super().__init__(Route, db)

    def get_with_segments(self, route_id: str) -> Optional[Route]:
        """Fetch route along with ordered segments."""
        return self.db.query(Route).filter(Route.id == route_id).first()
