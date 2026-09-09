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
        else:
            res = MultiObjectiveRouter.optimize_route(sim_engine.network, origin_station_id, destination_station_id)

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
