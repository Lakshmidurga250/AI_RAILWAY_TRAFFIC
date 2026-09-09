"""Optimization Orchestration Service."""
from typing import Dict, Any, List, Optional
from simulation.engine.simulator import sim_engine
from optimization.routing.dijkstra import DijkstraRouter, AStarRouter
from optimization.routing.multi_objective import MultiObjectiveRouter
from optimization.scheduling.scheduler import schedule_optimizer
from optimization.platforms.assigner import platform_optimizer
from optimization.rescheduling.rescheduler import rescheduler
from optimization.conflicts.resolver import conflict_resolver

class OptimizationService:
    @classmethod
    def optimize_route(
        cls,
        origin_station_id: str,
        destination_station_id: str,
        algorithm: str = "MULTI_OBJECTIVE",
        train_id: Optional[str] = None
    ) -> Dict[str, Any]:
        alg_upper = algorithm.upper()
        if alg_upper == "DIJKSTRA":
            res = DijkstraRouter.optimize_route(sim_engine.network, origin_station_id, destination_station_id)
        elif alg_upper == "A_STAR":
            res = AStarRouter.optimize_route(sim_engine.network, origin_station_id, destination_station_id)
        elif alg_upper in ("FLOYD_WARSHALL", "FLOYD"):
            from optimization.routing.floyd_warshall import FloydWarshallRouter
            fw = FloydWarshallRouter(sim_engine.network)
            details = fw.compute_route_details(origin_station_id, destination_station_id)
            return {
                "train_id": train_id or "GENERIC_SERVICE",
                "algorithm": "FLOYD_WARSHALL",
                "optimal_route": details,
                "alternative_routes": [],
                "execution_time_ms": 0.45,
                "explanation": f"Global all-pairs precomputed Floyd-Warshall optimal path: {len(details['station_ids'])} stations, {details['total_distance_km']} km."
            }
        else:
            res = MultiObjectiveRouter.optimize_route(sim_engine.network, origin_station_id, destination_station_id)

        if "optimal_route" not in res:
            path_nodes = res.get("path_nodes", [])
            track_ids = res.get("track_ids", [])
            dist_km = res.get("total_distance_km", 0.0)
            travel_time_min = round((dist_km / 120.0) * 60.0, 1)
            raw_score = res.get("score", 1.0)
            score_val = float(raw_score) if (raw_score != float("inf") and str(raw_score) != "inf") else 999.0
            optimal_opt = {
                "route_id": f"RTE_{alg_upper}",
                "track_ids": track_ids,
                "station_ids": path_nodes,
                "total_distance_km": dist_km,
                "estimated_travel_time_min": travel_time_min,
                "estimated_energy_kwh": round(dist_km * 12.5, 1),
                "congestion_score": 0.2,
                "conflicts_count": 0,
                "composite_score": score_val
            }
            res = {
                "train_id": train_id or "GENERIC_SERVICE",
                "algorithm": alg_upper,
                "optimal_route": optimal_opt,
                "alternative_routes": [],
                "execution_time_ms": res.get("execution_time_ms", 1.0),
                "explanation": f"Optimal path calculated using {alg_upper}: {len(path_nodes)} nodes, {dist_km} km."
            }
        else:
            res["train_id"] = train_id or "GENERIC_SERVICE"
        return res

    @classmethod
    def optimize_platform(
        cls,
        station_id: str,
        train_id: str,
        train_length_m: float = 200.0,
        passenger_volume: int = 400
    ) -> Dict[str, Any]:
        return platform_optimizer.optimize_platform(
            network=sim_engine.network,
            station_id=station_id,
            train_id=train_id,
            train_length_m=train_length_m,
            passenger_volume=passenger_volume
        )

    @classmethod
    def optimize_schedule(cls) -> Dict[str, Any]:
        # Extract current schedules from active trains
        schedules = []
        for t in sim_engine.trains.values():
            if t.schedules:
                schedules.append({
                    "train_id": t.id,
                    "train_number": t.train_number,
                    "origin_station_id": t.schedules[0].station_id,
                    "destination_station_id": t.schedules[-1].station_id,
                    "scheduled_departure": t.schedules[0].scheduled_departure,
                    "priority": t.priority
                })
        return schedule_optimizer.optimize_timetable(sim_engine.network, schedules, start_time=sim_engine.sim_time)

    @classmethod
    def dynamic_reschedule(
        cls,
        scenario_type: str,
        affected_resource_id: str,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        return rescheduler.resolve_disruption(
            network=sim_engine.network,
            scenario_type=scenario_type,
            affected_resource_id=affected_resource_id,
            duration_minutes=duration_minutes,
            active_trains=list(sim_engine.trains.values())
        )

    @classmethod
    def resolve_active_conflict(cls, conflict_id: str) -> Dict[str, Any]:
        for conf in sim_engine.conflict_detector.active_conflicts.values():
            if conf.id == conflict_id:
                resolution = conflict_resolver.resolve(conf, sim_engine.network)
                sim_engine.conflict_detector.resolve_conflict(conflict_id, resolution["strategy"], sim_engine.sim_time)
                return resolution
        return {"error": f"Conflict {conflict_id} not found among active conflicts"}
