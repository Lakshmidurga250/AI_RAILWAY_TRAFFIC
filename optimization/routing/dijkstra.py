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

        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        return {
            "algorithm": "DIJKSTRA",
            "weight_type": weight_type,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "path_nodes": path_nodes,
            "track_ids": [t.id for t in tracks],
            "total_distance_km": round(sum(t.length_km for t in tracks), 2),
            "score": round(path_length, 2),
            "execution_time_ms": round(exec_time_ms, 2)
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
            # Lat/lng approx to km: 1 deg lat ~ 111 km
            d_lat = (pos_u[0] - pos_v[0]) * 111.0
            d_lng = (pos_u[1] - pos_v[1]) * 111.0 * math.cos(math.radians(pos_u[0]))
            dist_km = math.sqrt(d_lat ** 2 + d_lng ** 2)
            # Heuristic in travel time minutes assuming max track speed 200 km/h
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

        exec_time_ms = (time.perf_counter() - start_t) * 1000.0

        return {
            "algorithm": "A_STAR",
            "weight_type": weight_type,
            "origin_id": origin_id,
            "destination_id": destination_id,
            "path_nodes": path_nodes,
            "track_ids": [t.id for t in tracks],
            "total_distance_km": round(sum(t.length_km for t in tracks), 2),
            "score": round(path_length, 2),
            "execution_time_ms": round(exec_time_ms, 2)
        }
