"""Train Management Service using TrainRepository and Simulation synchronization."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal
from backend.models.train import Train, TrainStatusHistory, TrainPosition
from backend.repositories.train_repository import TrainRepository
from backend.schemas.train import TrainCreate, TrainUpdate
from simulation.engine.simulator import sim_engine

class TrainService:
    """High-level service coordinating train fleet data, persistence, and live simulation."""

    @classmethod
    def list_trains(cls, status: Optional[str] = None, db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """List active fleet trains from simulation and repository."""
        # Active in simulation
        trains = []
        sim_ids = set()

        for t in sim_engine.trains.values():
            if status and t.status != status:
                continue
            sim_ids.add(t.id)
            curr_track_id = t.current_track.id if t.current_track else None
            origin_id = t.schedules[0].station_id if t.schedules else "N/A"
            dest_id = t.schedules[-1].station_id if t.schedules else "N/A"

            trains.append({
                "id": t.id,
                "train_number": t.train_number,
                "name": t.name,
                "train_type": t.train_type,
                "origin_station_id": origin_id,
                "destination_station_id": dest_id,
                "length_m": t.length_m,
                "weight_tons": t.mass_tons,
                "max_speed_kmh": t.max_speed_kmh,
                "acceleration_ms2": t.acceleration_ms2,
                "braking_ms2": t.braking_ms2,
                "passenger_capacity": t.passenger_capacity,
                "current_passengers": t.current_passengers,
                "priority": t.priority,
                "status": t.status,
                "current_speed_kmh": round(t.current_speed_kmh, 1),
                "current_track_id": curr_track_id,
                "current_platform_id": t.assigned_platform_id,
                "current_lat": t.current_lat,
                "current_lng": t.current_lng,
                "progress_percentage": round((t.current_track_index / max(1, len(t.route_tracks))) * 100.0, 1),
                "scheduled_departure": t.schedules[0].scheduled_departure if t.schedules else sim_engine.sim_time,
                "scheduled_arrival": t.schedules[-1].scheduled_arrival if t.schedules else sim_engine.sim_time,
                "current_delay_minutes": round(t.current_delay_minutes, 1),
                "cumulative_energy_kwh": round(t.cumulative_energy_kwh, 2),
                "regenerated_energy_kwh": round(t.regenerated_energy_kwh, 2),
                "schedules": [
                    {
                        "station_id": s.station_id,
                        "platform_id": s.platform_id,
                        "stop_sequence": s.stop_sequence,
                        "scheduled_arrival": s.scheduled_arrival,
                        "scheduled_departure": s.scheduled_departure,
                        "dwell_duration_seconds": s.dwell_duration_seconds,
                        "status": "COMPLETED" if s.is_completed else "PENDING"
                    }
                    for s in t.schedules
                ]
            })

        # Also retrieve non-simulated persistent database trains if db provided
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            db_trains = repo.search_trains(status=status)
            for dbt in db_trains:
                if dbt.id not in sim_ids:
                    trains.append({
                        "id": dbt.id,
                        "train_number": dbt.train_number,
                        "name": dbt.name,
                        "train_type": dbt.train_type,
                        "origin_station_id": dbt.origin_station_id,
                        "destination_station_id": dbt.destination_station_id,
                        "length_m": dbt.length_m,
                        "weight_tons": dbt.weight_tons,
                        "max_speed_kmh": dbt.max_speed_kmh,
                        "acceleration_ms2": dbt.acceleration_ms2,
                        "braking_ms2": dbt.braking_ms2,
                        "passenger_capacity": dbt.passenger_capacity,
                        "current_passengers": dbt.current_passengers,
                        "priority": dbt.priority,
                        "status": dbt.status,
                        "current_speed_kmh": dbt.current_speed_kmh,
                        "current_track_id": dbt.current_track_id,
                        "current_platform_id": dbt.current_platform_id,
                        "current_lat": dbt.current_lat,
                        "current_lng": dbt.current_lng,
                        "progress_percentage": dbt.progress_percentage,
                        "scheduled_departure": dbt.scheduled_departure,
                        "scheduled_arrival": dbt.scheduled_arrival,
                        "current_delay_minutes": dbt.current_delay_minutes,
                        "cumulative_energy_kwh": dbt.cumulative_energy_kwh,
                        "regenerated_energy_kwh": dbt.regenerated_energy_kwh,
                        "schedules": []
                    })
        finally:
            if close_db:
                db.close()

        return trains

    @classmethod
    def get_train(cls, train_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Fetch train detail by ID or train number."""
        for t in cls.list_trains(db=db):
            if t["id"] == train_id or t["train_number"] == train_id:
                return t
        return None

    @classmethod
    def create_train(cls, train_in: TrainCreate, db: Optional[Session] = None) -> Train:
        """Create a new train in the database repository and record initial status."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            db_train = Train(
                id=train_in.id,
                train_number=train_in.train_number,
                name=train_in.name,
                train_type=train_in.train_type,
                origin_station_id=train_in.origin_station_id,
                destination_station_id=train_in.destination_station_id,
                length_m=train_in.length_m,
                weight_tons=train_in.weight_tons,
                max_speed_kmh=train_in.max_speed_kmh,
                acceleration_ms2=train_in.acceleration_ms2,
                braking_ms2=train_in.braking_ms2,
                passenger_capacity=train_in.passenger_capacity,
                priority=train_in.priority,
                scheduled_departure=train_in.scheduled_departure,
                scheduled_arrival=train_in.scheduled_arrival,
                status="SCHEDULED"
            )
            created = repo.create(db_train)
            repo.record_status_transition(created.id, "SCHEDULED", reason="Initial timetable creation")
            return created
        finally:
            if close_db:
                db.close()

    @classmethod
    def update_train(cls, train_id: str, updates: TrainUpdate, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """Update train attributes across database and active simulation."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            db_train = repo.get(train_id)
            if db_train:
                update_dict = updates.model_dump(exclude_unset=True)
                if "status" in update_dict and update_dict["status"] != db_train.status:
                    repo.record_status_transition(train_id, update_dict["status"], reason="Operator update")
                repo.update(db_train, update_dict)

            # Update live simulation instance if running
            sim_train = sim_engine.trains.get(train_id)
            if sim_train:
                if updates.priority is not None:
                    sim_train.priority = updates.priority
                if updates.current_speed_kmh is not None:
                    sim_train.target_speed_kmh = updates.current_speed_kmh
                if updates.status is not None:
                    sim_train.status = updates.status

            return cls.get_train(train_id, db=db)
        finally:
            if close_db:
                db.close()

    @classmethod
    def delete_train(cls, train_id: str, db: Optional[Session] = None) -> bool:
        """Cancel and remove train from database and simulation."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            db_deleted = repo.delete(train_id)

            # Remove from simulation if present
            if train_id in sim_engine.trains:
                del sim_engine.trains[train_id]

            return db_deleted or (train_id in sim_engine.trains)
        finally:
            if close_db:
                db.close()

    @classmethod
    def update_train_priority(cls, train_id: str, new_priority: int, db: Optional[Session] = None) -> bool:
        """Update train priority in simulation and database repository."""
        t = sim_engine.trains.get(train_id)
        if t:
            t.priority = max(1, min(10, new_priority))

        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            train = repo.get(train_id)
            if train:
                train.priority = max(1, min(10, new_priority))
                db.commit()
            return True if (t or train) else False
        finally:
            if close_db:
                db.close()

    @classmethod
    def update_train_speed(cls, train_id: str, target_speed_kmh: float) -> bool:
        """Command speed update on live simulation train."""
        t = sim_engine.trains.get(train_id)
        if t:
            t.target_speed_kmh = max(0.0, min(t.max_speed_kmh, target_speed_kmh))
            return True
        return False

    @classmethod
    def emergency_stop(cls, train_id: str, reason: str = "EMERGENCY_STOP_COMMANDED", db: Optional[Session] = None) -> bool:
        """Execute emergency stop: brake train to 0 km/h, set STOPPED status, log history."""
        # 1. Stop simulation train
        t = sim_engine.trains.get(train_id)
        if t:
            t.target_speed_kmh = 0.0
            t.current_speed_kmh = 0.0
            t.status = "STOPPED"

        # 2. Persist in database
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            repo.record_status_transition(train_id, "STOPPED", reason=reason)
            return True
        finally:
            if close_db:
                db.close()

    @classmethod
    def get_status_history(cls, train_id: str, limit: int = 50, db: Optional[Session] = None) -> List[TrainStatusHistory]:
        """Query chronological status history for a train."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            return repo.get_status_history(train_id, limit=limit)
        finally:
            if close_db:
                db.close()

    @classmethod
    def get_positions_trail(cls, train_id: str, limit: int = 100, db: Optional[Session] = None) -> List[TrainPosition]:
        """Query spatial position history for track trail visualization."""
        close_db = False
        if db is None:
            db = SessionLocal()
            close_db = True
        try:
            repo = TrainRepository(db)
            return repo.get_positions_trail(train_id, limit=limit)
        finally:
            if close_db:
                db.close()
