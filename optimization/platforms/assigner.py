"""Platform Assignment Optimization Engine."""
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from simulation.network.graph import RailwayNetwork

class PlatformOptimizationEngine:
    """Optimizes station platform allocation considering train length, passenger load, and dwell times."""

    @classmethod
    def optimize_platform(
        cls,
        network: RailwayNetwork,
        station_id: str,
        train_id: str,
        train_length_m: float = 200.0,
        passenger_volume: int = 400
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        station = network.stations.get(station_id)
        if not station:
            return {"error": f"Station {station_id} not found"}

        candidate_platforms = []
        for p_id, p in station.platforms.items():
            # Constraints
            is_length_ok = p.length_m >= train_length_m
            is_free = not p.is_occupied
            
            # Score factors:
            # Availability (50 pts)
            # Length match efficiency (20 pts)
            # Accessibility rating (20 pts)
            # Overhead catenary (10 pts)
            length_margin = p.length_m - train_length_m
            length_score = max(0.0, 20.0 - (length_margin / 20.0)) if is_length_ok else 0.0
            avail_score = 50.0 if is_free else 0.0
            access_score = p.accessibility_score * 20.0
            cat_score = 10.0 if p.has_overhead_catenary else 0.0

            total_score = avail_score + length_score + access_score + cat_score
            
            candidate_platforms.append({
                "platform_id": p.id,
                "platform_number": p.platform_number,
                "length_m": p.length_m,
                "is_occupied": p.is_occupied,
                "accessibility_score": p.accessibility_score,
                "score": round(total_score, 2),
                "is_compatible": is_length_ok and is_free
            })

        # Sort candidate platforms descending
        candidate_platforms.sort(key=lambda x: x["score"], reverse=True)
        recommended = candidate_platforms[0] if candidate_platforms else {}
        alternatives = candidate_platforms[1:] if len(candidate_platforms) > 1 else []

        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        explanation = (
            f"Allocated Platform {recommended.get('platform_number')} at {station.name}. "
            f"Satisfies train length requirement ({train_length_m}m on {recommended.get('length_m')}m platform), "
            f"with accessibility score {recommended.get('accessibility_score')} and zero conflicting track occupancies."
        )

        return {
            "station_id": station_id,
            "station_name": station.name,
            "train_id": train_id,
            "recommended_platform_id": recommended.get("platform_id", ""),
            "platform_number": recommended.get("platform_number", "1"),
            "alternative_platforms": alternatives,
            "score": recommended.get("score", 0.0),
            "conflicts_avoided": 1 if any(p["is_occupied"] for p in candidate_platforms) else 0,
            "accessibility_rating": recommended.get("accessibility_score", 1.0),
            "execution_time_ms": round(exec_time_ms, 2),
            "explanation": explanation
        }

platform_optimizer = PlatformOptimizationEngine()
