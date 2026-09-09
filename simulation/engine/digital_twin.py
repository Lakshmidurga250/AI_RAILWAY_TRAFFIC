"""Railway Digital Twin: Synchronized Virtual Shadow of Network State."""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from simulation.engine.simulator import sim_engine, SimulationEngine
from simulation.events.event_bus import event_bus

class DigitalTwin:
    """Provides high-fidelity, event-sourced snapshot of the complete railway system."""
    
    def __init__(self, engine: SimulationEngine = sim_engine):
        self.engine = engine

    def get_live_snapshot(self) -> Dict[str, Any]:
        """Compile complete digital twin real-time state."""
        with self.engine.step_lock:
            # 1. Trains State
            trains_data = []
            for t in self.engine.trains.values():
                curr_track_id = t.current_track.id if t.current_track else None
                trains_data.append({
                    "id": t.id,
                    "train_number": t.train_number,
                    "name": t.name,
                    "type": t.train_type,
                    "status": t.status,
                    "speed_kmh": round(t.current_speed_kmh, 1),
                    "target_speed_kmh": round(t.target_speed_kmh, 1),
                    "current_track_id": curr_track_id,
                    "distance_along_track_km": round(t.distance_along_current_track_km, 2),
                    "lat": t.current_lat,
                    "lng": t.current_lng,
                    "priority": t.priority,
                    "passengers": t.current_passengers,
                    "capacity": t.passenger_capacity,
                    "delay_minutes": round(t.current_delay_minutes, 1),
                    "energy_kwh": round(t.cumulative_energy_kwh, 2),
                    "regenerated_kwh": round(t.regenerated_energy_kwh, 2),
                    "current_stop_index": t.current_stop_index,
                    "total_stops": len(t.schedules),
                    "stops": [
                        {
                            "station_id": s.station_id,
                            "scheduled_arrival": s.scheduled_arrival.isoformat() if s.scheduled_arrival else None,
                            "scheduled_departure": s.scheduled_departure.isoformat() if s.scheduled_departure else None,
                            "actual_arrival": s.actual_arrival.isoformat() if s.actual_arrival else None,
                            "actual_departure": s.actual_departure.isoformat() if s.actual_departure else None,
                            "completed": s.is_completed
                        }
                        for s in t.schedules
                    ]
                })

            # 2. Tracks State
            tracks_data = []
            for track in self.engine.network.tracks.values():
                tracks_data.append({
                    "id": track.id,
                    "name": track.name,
                    "source": track.source_node,
                    "target": track.target_node,
                    "status": track.status.value if hasattr(track.status, "value") else track.status,
                    "occupying_trains": track.current_train_ids,
                    "is_occupied": len(track.current_train_ids) > 0,
                    "is_maintenance": track.is_maintenance_closed,
                    "speed_restriction_kmh": track.speed_restriction_kmh
                })

            # 3. Signals State
            signals_data = []
            for track in self.engine.network.tracks.values():
                for sig in track.signals:
                    signals_data.append({
                        "id": sig.id,
                        "track_id": track.id,
                        "aspect": sig.aspect.value if hasattr(sig.aspect, "value") else sig.aspect,
                        "is_faulty": sig.is_faulty
                    })

            # 4. Stations & Platforms State
            stations_data = []
            for st in self.engine.network.stations.values():
                platforms_data = []
                for p in st.platforms.values():
                    platforms_data.append({
                        "id": p.id,
                        "number": p.platform_number,
                        "is_occupied": p.is_occupied,
                        "current_train_id": p.current_train_id,
                        "status": p.status
                    })
                stations_data.append({
                    "id": st.id,
                    "name": st.name,
                    "code": st.code,
                    "zone": st.zone,
                    "occupancy": st.current_occupancy,
                    "capacity": st.passenger_capacity,
                    "status": st.status,
                    "platforms": platforms_data
                })

            # 5. Conflicts State
            conflicts_data = [
                conf.to_dict()
                for conf in self.engine.conflict_detector.active_conflicts.values()
            ]

            # 6. Simulation Summary
            summary = self.engine.get_status_summary()

            return {
                "timestamp": self.engine.sim_time.isoformat(),
                "simulation": summary,
                "trains": trains_data,
                "tracks": tracks_data,
                "signals": signals_data,
                "stations": stations_data,
                "conflicts": conflicts_data,
                "recent_events": [e.model_dump(mode="json") for e in event_bus.get_history(limit=25)]
            }

digital_twin = DigitalTwin(sim_engine)
