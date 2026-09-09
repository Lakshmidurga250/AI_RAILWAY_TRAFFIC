"""Congestion Prediction Engine for Stations, Tracks, and Junctions."""
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from simulation.network.graph import RailwayNetwork

class CongestionPredictor:
    """Forecasts spatial and network resource congestion across multi-time horizons."""

    @classmethod
    def predict_congestion(
        cls,
        resource_type: str,
        resource_id: str,
        network: RailwayNetwork,
        horizon_minutes: int = 15,
        active_trains_count: int = 6
    ) -> Dict[str, Any]:
        """Compute congestion score, classification, and mitigation recommendations."""
        base_score = 0.25
        name = resource_id
        affected = [resource_id]
        recs = []

        if resource_type.upper() == "STATION":
            st = network.stations.get(resource_id)
            if st:
                name = st.name
                occupancy_ratio = st.current_occupancy / max(1, st.passenger_capacity)
                occupied_platforms = sum(1 for p in st.platforms.values() if p.is_occupied)
                platform_ratio = occupied_platforms / max(1, len(st.platforms))
                base_score = (occupancy_ratio * 0.4) + (platform_ratio * 0.6)
                
                # Check connected tracks
                for t in network.tracks.values():
                    if t.source_node == resource_id or t.target_node == resource_id:
                        if len(t.current_train_ids) > 0:
                            affected.append(t.id)

        elif resource_type.upper() == "TRACK":
            track = network.tracks.get(resource_id)
            if track:
                name = track.name
                trains_on_track = len(track.current_train_ids)
                base_score = min(1.0, trains_on_track * 0.5)
                if track.is_maintenance_closed:
                    base_score = 1.0
                elif track.speed_restriction_kmh:
                    base_score += 0.25

        elif resource_type.upper() == "JUNCTION":
            jct = network.junctions.get(resource_id)
            if jct:
                name = jct.name
                base_score = min(1.0, (jct.current_load / max(1, jct.max_throughput_tph)) * 1.2)

        # Scale with horizon (traffic buildup or dispersal)
        horizon_factor = 1.0 + (horizon_minutes / 60.0) * 0.2
        final_score = min(0.98, max(0.05, base_score * horizon_factor))

        # Classify severity
        if final_score >= 0.80:
            level = "CRITICAL"
            prob = 0.92
            duration_min = 45.0
            recs = [
                f"Activate dynamic rerouting around {name}",
                "Institute 4-minute minimum headway separation",
                "Hold low-priority freight services at outer sidings"
            ]
        elif final_score >= 0.60:
            level = "HIGH"
            prob = 0.84
            duration_min = 30.0
            recs = [
                f"Prepare platform reassignment at {name}",
                "Speed harmonize inbound trains to 80 km/h"
            ]
        elif final_score >= 0.35:
            level = "MEDIUM"
            prob = 0.70
            duration_min = 15.0
            recs = ["Monitor approach signals and dwell adherence"]
        else:
            level = "LOW"
            prob = 0.50
            duration_min = 5.0
            recs = ["Normal operations; maintain scheduled timetable"]

        confidence = round(max(0.72, min(0.95, 0.90 - (horizon_minutes / 200.0))), 2)

        return {
            "resource_type": resource_type.upper(),
            "resource_id": resource_id,
            "resource_name": name,
            "horizon_minutes": horizon_minutes,
            "congestion_score": round(final_score, 3),
            "congestion_level": level,
            "probability": prob,
            "expected_duration_minutes": duration_min,
            "affected_resources": affected,
            "recommendations": recs,
            "confidence": confidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

congestion_predictor = CongestionPredictor()
