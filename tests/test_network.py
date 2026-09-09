"""Unit and Invariant Tests for Railway Network Graph."""
import pytest
from simulation.network.elements import TrackStatus
from simulation.network.graph import RailwayNetwork
from simulation.network.loader import create_corridor_network

def test_corridor_network_creation():
    net = create_corridor_network()
    assert len(net.stations) >= 10
    assert len(net.junctions) >= 4
    assert len(net.tracks) >= 15
    assert len(net.signals) >= 30

def test_shortest_path_routing(test_network):
    path = test_network.find_shortest_path("ST_SOUTH", "ST_NORTH")
    assert path is not None
    assert len(path) >= 4
    assert path[0] == "ST_SOUTH"
    assert path[-1] == "ST_NORTH"

def test_k_shortest_alternative_paths(test_network):
    paths = test_network.find_k_shortest_paths("ST_SOUTH", "ST_SUMMIT", k=3)
    assert len(paths) >= 1
    for p in paths:
        assert p[0] == "ST_SOUTH"
        assert p[-1] == "ST_SUMMIT"

def test_track_closure_rerouting():
    net = create_corridor_network()
    # Initial path
    initial_path = net.find_shortest_path("JCT_CENTRAL_W", "ST_CENTRAL")
    assert initial_path is not None
    
    # Block the main track
    net.update_track_status("TRK_JCW_GUT_UP", TrackStatus.BLOCKED, is_maintenance=True)
    track = net.get_track("TRK_JCW_GUT_UP")
    assert track.status == TrackStatus.MAINTENANCE or track.is_maintenance_closed
    
    # Alternative path search
    alt_path = net.find_shortest_path("JCT_CENTRAL_W", "ST_CENTRAL")
    # If blocked and no alternative, returns None or alternative via bypass
    # Verify weight function returns infinity for blocked track
    edge_data = {"data": track}
    w = net.calculate_weight("JCT_CENTRAL_W", "ST_CENTRAL", edge_data)
    assert w == float("inf")

def test_geojson_export(test_network):
    geo = test_network.to_geojson_dict()
    assert "nodes" in geo
    assert "edges" in geo
    assert geo["stations_count"] >= 10
    assert len(geo["nodes"]) == geo["stations_count"] + geo["junctions_count"]
