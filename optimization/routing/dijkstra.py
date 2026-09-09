"""Dijkstra and A* Railway Route Optimizers."""
import math
import time
from typing import List, Dict, Any, Optional
import networkx as nx
from simulation.network.graph import RailwayNetwork
from simulation.network.elements import TrackEdge

class DijkstraRouter:
    """Computes exact lowest-cost path based on configurable edge weights."""

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        weight_type: str = "travel_time"
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()
        
        def weight_fn(u, v, d):
            return network.calculate_weight(u, v, d, weight_type)

        try:
            path_nodes = nx.dijkstra_path(network.graph, origin_id, destination_id, weight=weight_fn)
            path_length = nx.dijkstra_path_length(network.graph, origin_id, destination_id, weight=weight_fn)
            tracks = network.path_to_tracks(path_nodes)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path_nodes = []
            tracks = []
            path_length = float("inf")

        dist_km = sum(t.length_km for t in tracks)
        time_min = sum((t.length_km / max(40.0, t.max_speed_kmh)) * 60.0 for t in tracks)
        energy_kwh = sum(t.length_km * 12.0 for t in tracks)
        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        optimal = {
            "route_id": "RTE_DIJKSTRA_1",
            "track_ids": [t.id for t in tracks],
            "station_ids": [n for n in path_nodes if n in network.stations],
            "total_distance_km": round(dist_km, 2),
            "estimated_travel_time_min": round(time_min, 1),
            "estimated_energy_kwh": round(energy_kwh, 1),
            "congestion_score": 0.2,
            "conflicts_count": 0,
            "composite_score": round(path_length, 2)
        }

        return {
            "train_id": "SERVICE_OPT",
            "algorithm": "DIJKSTRA",
            "optimal_route": optimal,
            "alternative_routes": [],
            "execution_time_ms": round(exec_time_ms, 2),
            "explanation": f"Dijkstra computed exact shortest path spanning {optimal['total_distance_km']} km."
        }

class AStarRouter:
    """A* router using Euclidean distance heuristic for spatial rail graphs."""

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        weight_type: str = "travel_time"
    ) -> Dict[str, Any]:
        start_t = time.perf_counter()

        def heuristic(u, v):
            pos_u = network.node_positions.get(u, (0, 0))
            pos_v = network.node_positions.get(v, (0, 0))
            d_lat = (pos_u[0] - pos_v[0]) * 111.0
            d_lng = (pos_u[1] - pos_v[1]) * 111.0 * math.cos(math.radians(pos_u[0]))
            dist_km = math.sqrt(d_lat ** 2 + d_lng ** 2)
            return (dist_km / 200.0) * 60.0

        def weight_fn(u, v, d):
            return network.calculate_weight(u, v, d, weight_type)

        try:
            path_nodes = nx.astar_path(network.graph, origin_id, destination_id, heuristic=heuristic, weight=weight_fn)
            path_length = nx.astar_path_length(network.graph, origin_id, destination_id, heuristic=heuristic, weight=weight_fn)
            tracks = network.path_to_tracks(path_nodes)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path_nodes = []
            tracks = []
            path_length = float("inf")

        dist_km = sum(t.length_km for t in tracks)
        time_min = sum((t.length_km / max(40.0, t.max_speed_kmh)) * 60.0 for t in tracks)
        energy_kwh = sum(t.length_km * 12.0 for t in tracks)
        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        optimal = {
            "route_id": "RTE_ASTAR_1",
            "track_ids": [t.id for t in tracks],
            "station_ids": [n for n in path_nodes if n in network.stations],
            "total_distance_km": round(dist_km, 2),
            "estimated_travel_time_min": round(time_min, 1),
            "estimated_energy_kwh": round(energy_kwh, 1),
            "congestion_score": 0.15,
            "conflicts_count": 0,
            "composite_score": round(path_length, 2)
        }

        return {
            "train_id": "SERVICE_OPT",
            "algorithm": "A_STAR",
            "optimal_route": optimal,
            "alternative_routes": [],
            "execution_time_ms": round(exec_time_ms, 2),
            "explanation": f"A* heuristic guided pathfinding converged in {exec_time_ms:.2f} ms."
        }
