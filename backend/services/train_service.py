"""Train Management Service."""
from typing import List, Dict, Any, Optional
from simulation.engine.simulator import sim_engine
from simulation.trains.train import SimulationTrain, PlannedStop

class TrainService:
    @classmethod
    def list_trains(cls, status: Optional[str] = None) -> List[Dict[str, Any]]:
        trains = []
        for t in sim_engine.trains.values():
            if status and t.status != status:
                continue
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
        return trains

    @classmethod
    def get_train(cls, train_id: str) -> Optional[Dict[str, Any]]:
        for t in cls.list_trains():
            if t["id"] == train_id or t["train_number"] == train_id:
                return t
        return None

    @classmethod
    def update_train_priority(cls, train_id: str, new_priority: int) -> bool:
        t = sim_engine.trains.get(train_id)
        if t:
            t.priority = max(1, min(10, new_priority))
            return True
        return False

    @classmethod
    def update_train_speed(cls, train_id: str, target_speed_kmh: float) -> bool:
        t = sim_engine.trains.get(train_id)
        if t:
            t.target_speed_kmh = max(0.0, min(t.max_speed_kmh, target_speed_kmh))
            return True
        return False
