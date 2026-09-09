"""Railway Network Service."""
from typing import List, Dict, Any, Optional
from simulation.engine.simulator import sim_engine
from simulation.network.elements import TrackStatus

class NetworkService:
    @classmethod
    def get_stations(cls) -> List[Dict[str, Any]]:
        stations = []
        for s in sim_engine.network.stations.values():
            platforms = [
                {
                    "id": p.id,
                    "station_id": p.station_id,
                    "platform_number": p.platform_number,
                    "length": p.length_m,
                    "capacity": p.capacity,
                    "is_occupied": p.is_occupied,
                    "current_train_id": p.current_train_id,
                    "status": p.status,
                    "has_overhead_catenary": p.has_overhead_catenary
                }
                for p in s.platforms.values()
            ]
            stations.append({
                "id": s.id,
                "name": s.name,
                "code": s.code,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "zone": s.zone,
                "passenger_capacity": s.passenger_capacity,
                "current_occupancy": s.current_occupancy,
                "status": s.status,
                "platforms": platforms
            })
        return stations

    @classmethod
    def get_tracks(cls) -> List[Dict[str, Any]]:
        tracks = []
        for t in sim_engine.network.tracks.values():
            tracks.append({
                "id": t.id,
                "name": t.name,
                "source_node": t.source_node,
                "target_node": t.target_node,
                "length": t.length_km,
                "max_speed": t.max_speed_kmh,
                "gradient": t.gradient_percent,
                "electrified": t.electrified,
                "track_type": t.track_type,
                "is_bidirectional": t.is_bidirectional,
                "status": t.status.value if hasattr(t.status, "value") else t.status,
                "current_train_id": t.current_train_ids[0] if t.current_train_ids else None,
                "speed_restriction": t.speed_restriction_kmh
            })
        return tracks

    @classmethod
    def get_signals(cls) -> List[Dict[str, Any]]:
        signals = []
        for track in sim_engine.network.tracks.values():
            for sig in track.signals:
                signals.append({
                    "id": sig.id,
                    "track_id": sig.track_id,
                    "location_km": sig.location_km,
                    "aspect": sig.aspect.value if hasattr(sig.aspect, "value") else sig.aspect,
                    "is_faulty": sig.is_faulty
                })
        return signals

    @classmethod
    def get_network_graph(cls) -> Dict[str, Any]:
        return sim_engine.network.to_geojson_dict()

    @classmethod
    def update_track_status(cls, track_id: str, status_str: str, speed_limit: Optional[float] = None) -> bool:
        track = sim_engine.network.tracks.get(track_id)
        if not track:
            return False
        try:
            status_enum = TrackStatus(status_str)
            sim_engine.network.update_track_status(track_id, status_enum, is_maintenance=(status_enum == TrackStatus.MAINTENANCE))
            if speed_limit is not None:
                track.speed_restriction_kmh = speed_limit
            return True
        except ValueError:
            return False
