"""Optimization Algorithm Suite Unit Tests."""
from optimization.routing.dijkstra import DijkstraRouter, AStarRouter
from optimization.routing.multi_objective import MultiObjectiveRouter
from optimization.platforms.assigner import PlatformOptimizationEngine
from optimization.scheduling.scheduler import ScheduleOptimizer
from optimization.rescheduling.rescheduler import DynamicRescheduler

def test_dijkstra_vs_astar(test_network):
    dijk = DijkstraRouter.optimize_route(test_network, "ST_SOUTH", "ST_NORTH")
    astar = AStarRouter.optimize_route(test_network, "ST_SOUTH", "ST_NORTH")
    
    assert dijk["path_nodes"] is not None
    assert astar["path_nodes"] is not None
    assert dijk["path_nodes"][0] == "ST_SOUTH"
    assert astar["path_nodes"][-1] == "ST_NORTH"
    assert dijk["total_distance_km"] > 0

def test_multi_objective_pareto(test_network):
    res = MultiObjectiveRouter.optimize_route(test_network, "ST_SOUTH", "ST_SUMMIT")
    assert "optimal_route" in res
    assert "composite_score" in res["optimal_route"]
    assert res["optimal_route"]["total_distance_km"] > 0
    assert "explanation" in res

def test_platform_optimizer(test_network):
    res = PlatformOptimizationEngine.optimize_platform(
        network=test_network,
        station_id="ST_CENTRAL",
        train_id="TR_101",
        train_length_m=200.0
    )
    assert "recommended_platform_id" in res
    assert res["score"] > 0
    assert "accessibility_rating" in res

def test_dynamic_rescheduling_delay_reduction(test_network):
    res = DynamicRescheduler.resolve_disruption(
        network=test_network,
        scenario_type="TRACK_CLOSURE",
        affected_resource_id="TRK_JCW_GUT_UP",
        duration_minutes=60
    )
    assert res["delay_reduction_percentage"] > 0
    assert res["baseline_delay_minutes"] > res["optimized_delay_minutes"]
    assert "explanation" in res

def test_floyd_warshall_all_pairs(test_network):
    from optimization.routing.floyd_warshall import FloydWarshallRouter
    fw = FloydWarshallRouter(test_network)
    dist = fw.get_distance("ST_CENTRAL", "ST_NORTH")
    assert dist > 0.0 and dist != float("inf")
    path = fw.get_shortest_path("ST_CENTRAL", "ST_NORTH")
    assert path is not None
    assert path[0] == "ST_CENTRAL"
    assert path[-1] == "ST_NORTH"
    details = fw.compute_route_details("ST_CENTRAL", "ST_NORTH")
    assert details["total_distance_km"] == round(dist, 2)
    assert len(details["track_ids"]) > 0
