"""Railway Network Graph Representation using NetworkX."""
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
import math
from simulation.network.elements import (
    StationNode, JunctionNode, TrackEdge, PlatformElement,
    SignalElement, SwitchElement, TrackStatus, SignalAspect
)

class RailwayNetwork:
    """Directed MultiGraph model of the railway infrastructure."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.stations: Dict[str, StationNode] = {}
        self.junctions: Dict[str, JunctionNode] = {}
        self.tracks: Dict[str, TrackEdge] = {}
        self.signals: Dict[str, SignalElement] = {}
        self.switches: Dict[str, SwitchElement] = {}
        self.node_positions: Dict[str, Tuple[float, float]] = {}  # id -> (lat, lng)

    def add_station(self, station: StationNode):
        """Add a passenger station node."""
        self.stations[station.id] = station
        self.node_positions[station.id] = (station.latitude, station.longitude)
        self.graph.add_node(
            station.id,
            node_type="STATION",
            name=station.name,
            code=station.code,
            lat=station.latitude,
            lng=station.longitude,
            platforms=len(station.platforms),
            data=station
        )

    def add_junction(self, junction: JunctionNode):
        """Add a railway junction node."""
        self.junctions[junction.id] = junction
        self.node_positions[junction.id] = (junction.latitude, junction.longitude)
        self.graph.add_node(
            junction.id,
            node_type="JUNCTION",
            name=junction.name,
            lat=junction.latitude,
            lng=junction.longitude,
            data=junction
        )

    def add_track(self, track: TrackEdge):
        """Add a track segment as directed edge(s)."""
        self.tracks[track.id] = track
        # Forward edge
        self.graph.add_edge(
            track.source_node,
            track.target_node,
            key=track.id,
            track_id=track.id,
            length=track.length_km,
            max_speed=track.max_speed_kmh,
            gradient=track.gradient_percent,
            electrified=track.electrified,
            track_type=track.track_type,
            status=track.status,
            data=track
        )
        
        # If bidirectional, add reverse edge with same track reference or separate ID
        if track.is_bidirectional:
            rev_key = f"{track.id}_rev"
            self.graph.add_edge(
                track.target_node,
                track.source_node,
                key=rev_key,
                track_id=track.id,
                length=track.length_km,
                max_speed=track.max_speed_kmh,
                gradient=-track.gradient_percent,
                electrified=track.electrified,
                track_type=track.track_type,
                status=track.status,
                data=track
            )

        # Register signals on track
        for signal in track.signals:
            self.signals[signal.id] = signal

    def get_track(self, track_id: str) -> Optional[TrackEdge]:
        return self.tracks.get(track_id)

    def get_station(self, station_id: str) -> Optional[StationNode]:
        return self.stations.get(station_id)

    def get_junction(self, junction_id: str) -> Optional[JunctionNode]:
        return self.junctions.get(junction_id)

    def update_track_status(self, track_id: str, status: TrackStatus, is_maintenance: bool = False):
        """Update track status in data model and graph."""
        track = self.tracks.get(track_id)
        if track:
            track.status = status
            track.is_maintenance_closed = is_maintenance
            for u, v, k, d in self.graph.edges(keys=True, data=True):
                if d.get("track_id") == track_id:
                    d["status"] = status

    def calculate_weight(self, u: str, v: str, edge_data: dict, weight_type: str = "travel_time") -> float:
        """Calculate dynamic weight based on distance, speed limits, status, and congestion."""
        track: TrackEdge = edge_data.get("data")
        if not track:
            return float("inf")

        # Infeasible if blocked or maintenance closed
        if track.is_maintenance_closed or track.status in (TrackStatus.BLOCKED, TrackStatus.MAINTENANCE):
            return float("inf")

        effective_speed = track.speed_restriction_kmh or track.max_speed_kmh
        if effective_speed <= 0:
            return float("inf")

        travel_time_hours = track.length_km / effective_speed
        travel_time_minutes = travel_time_hours * 60.0

        if weight_type == "distance":
            return track.length_km
        elif weight_type == "travel_time":
            # Penalty for occupied track
            occupancy_penalty = len(track.current_train_ids) * 5.0  # +5 min per train ahead
            return travel_time_minutes + occupancy_penalty
        elif weight_type == "energy":
            # Basic energy proxy: distance * (1 + 0.05 * gradient)
            gradient_factor = max(0.2, 1.0 + (track.gradient_percent / 100.0) * 2.0)
            return track.length_km * gradient_factor
        elif weight_type == "composite":
            return (travel_time_minutes * 0.5) + (track.length_km * 0.3) + (len(track.current_train_ids) * 10.0)
        
        return track.length_km

    def find_shortest_path(self, origin_id: str, destination_id: str, weight_type: str = "travel_time") -> Optional[List[str]]:
        """Find the shortest route sequence of node IDs."""
        try:
            def weight_func(u, v, d):
                return self.calculate_weight(u, v, d, weight_type)

            path = nx.shortest_path(self.graph, source=origin_id, target=destination_id, weight=weight_func)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_k_shortest_paths(self, origin_id: str, destination_id: str, k: int = 3, weight_type: str = "travel_time") -> List[List[str]]:
        """Find k alternative routes between two nodes."""
        try:
            # Build simple DiGraph collapsing multigraph parallel edges to minimum weight
            simple_g = nx.DiGraph()
            for u, v, k_id, d in self.graph.edges(keys=True, data=True):
                w = self.calculate_weight(u, v, d, weight_type)
                if w < float("inf"):
                    if simple_g.has_edge(u, v):
                        if w < simple_g[u][v]["weight"]:
                            simple_g[u][v]["weight"] = w
                    else:
                        simple_g.add_edge(u, v, weight=w)

            paths_gen = nx.shortest_simple_paths(simple_g, source=origin_id, target=destination_id, weight="weight")
            result = []
            for _, path in zip(range(k), paths_gen):
                result.append(path)
            return result
        except (nx.NetworkXNoPath, nx.NodeNotFound, nx.NetworkXError):
            return []

    def path_to_tracks(self, path: List[str]) -> List[TrackEdge]:
        """Convert a sequence of node IDs to a sequence of TrackEdge objects."""
        track_list = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            best_track = None
            min_len = float("inf")
            for _, _, d in self.graph.out_edges(u, data=True):
                if d.get("track_id") and self.tracks[d["track_id"]].target_node == v:
                    t = self.tracks[d["track_id"]]
                    if t.length_km < min_len:
                        min_len = t.length_km
                        best_track = t
            if best_track:
                track_list.append(best_track)
        return track_list

    def to_geojson_dict(self) -> Dict[str, Any]:
        """Export network topology to clean JSON format for frontend maps and graphs."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": data.get("name", node_id),
                "type": data.get("node_type", "UNKNOWN"),
                "lat": data.get("lat", 0.0),
                "lng": data.get("lng", 0.0),
                "code": data.get("code", "")
            })
            
        edges = []
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            track: TrackEdge = data.get("data")
            if track:
                u_pos = self.node_positions.get(u, (0, 0))
                v_pos = self.node_positions.get(v, (0, 0))
                edges.append({
                    "id": track.id,
                    "name": track.name,
                    "source": u,
                    "target": v,
                    "length_km": track.length_km,
                    "max_speed_kmh": track.max_speed_kmh,
                    "status": track.status.value if hasattr(track.status, "value") else track.status,
                    "coordinates": [list(u_pos), list(v_pos)],
                    "current_trains": track.current_train_ids,
                    "electrified": track.electrified
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "stations_count": len(self.stations),
            "tracks_count": len(self.tracks),
            "junctions_count": len(self.junctions)
        }
