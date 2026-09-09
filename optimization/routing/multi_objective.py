"""Multi-Objective Route Optimization and Pareto Scoring."""
import time
from typing import List, Dict, Any, Optional
from simulation.network.graph import RailwayNetwork
from simulation.network.elements import TrackEdge

class MultiObjectiveRouter:
    """Evaluates candidate paths across travel time, delay risk, congestion, and energy."""

    DEFAULT_WEIGHTS = {
        "travel_time": 0.40,
        "delay_risk": 0.25,
        "congestion": 0.20,
        "energy": 0.15
    }

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        w = weights or cls.DEFAULT_WEIGHTS

        # Retrieve up to 4 alternative paths
        candidate_paths = network.find_k_shortest_paths(origin_id, destination_id, k=4, weight_type="travel_time")
        if not candidate_paths:
            # Fallback to simple shortest
            sp = network.find_shortest_path(origin_id, destination_id)
            if sp:
                candidate_paths = [sp]

        evaluated_options = []
        for idx, path in enumerate(candidate_paths):
            tracks = network.path_to_tracks(path)
            dist_km = sum(t.length_km for t in tracks)
            
            # 1. Travel time
            travel_time_min = sum((t.length_km / max(40.0, t.max_speed_kmh)) * 60.0 for t in tracks)
            
            # 2. Congestion score
            congestion_vals = [len(t.current_train_ids) * 0.3 for t in tracks]
            avg_congestion = min(1.0, (sum(congestion_vals) / max(1, len(tracks)))) if tracks else 0.0
            
            # 3. Energy estimate
            energy_kwh = sum(t.length_km * (12.0 + t.gradient_percent * 2.0) for t in tracks)
            
            # 4. Conflict risk
            conflicts_count = sum(1 for t in tracks if len(t.current_train_ids) > 1)
            
            # Composite normalized score (lower is better)
            score = (
                (travel_time_min * w.get("travel_time", 0.4)) +
                (avg_congestion * 50.0 * w.get("congestion", 0.2)) +
                ((energy_kwh / 10.0) * w.get("energy", 0.15)) +
                (conflicts_count * 20.0 * w.get("delay_risk", 0.25))
            )

            evaluated_options.append({
                "route_id": f"RTE_OPT_{idx + 1}",
                "path_nodes": path,
                "track_ids": [t.id for t in tracks],
                "total_distance_km": round(dist_km, 2),
                "estimated_travel_time_min": round(travel_time_min, 1),
                "estimated_energy_kwh": round(energy_kwh, 1),
                "congestion_score": round(avg_congestion, 2),
                "conflicts_count": conflicts_count,
                "composite_score": round(score, 2)
            })

        # Sort by best composite score
        evaluated_options.sort(key=lambda x: x["composite_score"])
        optimal = evaluated_options[0] if evaluated_options else {}
        alternatives = evaluated_options[1:] if len(evaluated_options) > 1 else []

        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        explanation = (
            f"Selected {optimal.get('route_id')} as optimal path: distance {optimal.get('total_distance_km')} km, "
            f"estimated time {optimal.get('estimated_travel_time_min')} min, "
            f"bypassing high-density corridors with {optimal.get('conflicts_count')} active conflicts."
        )

        return {
            "algorithm": "MULTI_OBJECTIVE_PARETO",
            "origin_id": origin_id,
            "destination_id": destination_id,
            "optimal_route": optimal,
            "alternative_routes": alternatives,
            "execution_time_ms": round(exec_time_ms, 2),
            "explanation": explanation
        }
