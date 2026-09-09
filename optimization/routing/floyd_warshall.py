"""Floyd-Warshall All-Pairs Shortest Path Router for Railway Networks.

Computes global distance matrices and all-pairs optimal paths for high-frequency routing queries.
"""
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
from simulation.network.graph import RailwayNetwork

class FloydWarshallRouter:
    """Computes and caches all-pairs shortest path matrices across the railway network."""

    def __init__(self, network: RailwayNetwork):
        self.network = network
        self.dist_matrix: Dict[str, Dict[str, float]] = {}
        self.pred_matrix: Dict[str, Dict[str, Optional[str]]] = {}
        self._compute_all_pairs()

    def _compute_all_pairs(self):
        """Execute Floyd-Warshall dynamic programming across simple directed projection."""
        simple_graph = self.network.to_simple_digraph(weight_attribute="length_km")
        nodes = list(simple_graph.nodes())
        inf = float("inf")

        # Initialize matrices
        for u in nodes:
            self.dist_matrix[u] = {v: inf for v in nodes}
            self.pred_matrix[u] = {v: None for v in nodes}
            self.dist_matrix[u][u] = 0.0

        for u, v, data in simple_graph.edges(data=True):
            w = data.get("length_km", 1.0)
            if w < self.dist_matrix[u][v]:
                self.dist_matrix[u][v] = w
                self.pred_matrix[u][v] = u

        # Dynamic programming triple loop
        for k in nodes:
            for i in nodes:
                for j in nodes:
                    if self.dist_matrix[i][k] + self.dist_matrix[k][j] < self.dist_matrix[i][j]:
                        self.dist_matrix[i][j] = self.dist_matrix[i][k] + self.dist_matrix[k][j]
                        self.pred_matrix[i][j] = self.pred_matrix[k][j]

    def get_shortest_path(self, origin: str, destination: str) -> Optional[List[str]]:
        """Reconstruct shortest path node sequence from predecessor matrix."""
        if origin not in self.dist_matrix or destination not in self.dist_matrix:
            return None
        if self.dist_matrix[origin][destination] == float("inf"):
            return None
        if origin == destination:
            return [origin]

        path = []
        curr = destination
        while curr is not None:
            path.append(curr)
            if curr == origin:
                break
            curr = self.pred_matrix[origin][curr]

        if not path or path[-1] != origin:
            return None
        return path[::-1]

    def get_distance(self, origin: str, destination: str) -> float:
        """O(1) lookup of shortest distance between any station pair."""
        return self.dist_matrix.get(origin, {}).get(destination, float("inf"))

    def compute_route_details(self, origin: str, destination: str) -> Dict[str, Any]:
        """Return comprehensive route characteristics for Floyd-Warshall path."""
        path = self.get_shortest_path(origin, destination)
        if not path or len(path) < 2:
            return {
                "route_id": "RTE_FLOYD_WARSHALL_NONE",
                "track_ids": [],
                "station_ids": [origin],
                "total_distance_km": 0.0,
                "estimated_travel_time_min": 0.0,
                "estimated_energy_kwh": 0.0,
                "composite_score": 9999.0
            }

        tracks = self.network.path_to_tracks(path)
        dist_km = sum(t.length_km for t in tracks)
        travel_time_min = sum((t.length_km / max(40.0, t.max_speed_kmh)) * 60.0 for t in tracks)
        energy_kwh = sum(t.length_km * 12.5 for t in tracks)

        return {
            "route_id": f"RTE_FW_{origin}_{destination}",
            "track_ids": [t.id for t in tracks],
            "station_ids": path,
            "total_distance_km": round(dist_km, 2),
            "estimated_travel_time_min": round(travel_time_min, 2),
            "estimated_energy_kwh": round(energy_kwh, 2),
            "composite_score": round(dist_km * 10.0 + travel_time_min * 2.0, 2)
        }
