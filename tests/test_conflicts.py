"""Conflict Detection and Resolution Arbiter Tests."""
from datetime import datetime, timezone
from simulation.conflicts.detector import ConflictDetector, ConflictRecord
from simulation.network.loader import create_corridor_network
from simulation.trains.train import SimulationTrain
from optimization.conflicts.resolver import ConflictResolver

def test_headway_conflict_detection():
    net = create_corridor_network()
    detector = ConflictDetector(net)
    
    # Place two trains on the same track with insufficient headway (< 2.0 km)
    track = list(net.tracks.values())[0]
    
    t1 = SimulationTrain("T1", "TR-100", "Lead", max_speed_kmh=120.0)
    t2 = SimulationTrain("T2", "TR-200", "Follower", max_speed_kmh=120.0)
    
    t1.route_tracks = [track]
    t2.route_tracks = [track]
    track.current_train_ids = [t1.id, t2.id]
    
    t1.distance_along_current_track_km = 3.0
    t2.distance_along_current_track_km = 3.5  # 0.5 km apart (headway violation)
    
    sim_time = datetime.now(timezone.utc)
    conflicts = detector.scan_conflicts([t1, t2], sim_time)
    
    assert len(conflicts) >= 1
    assert any(c.conflict_type == "HEADWAY_VIOLATION" for c in conflicts)

def test_conflict_resolution():
    net = create_corridor_network()
    conf = ConflictRecord(
        conflict_type="HEADWAY_VIOLATION",
        severity="HIGH",
        location_type="TRACK",
        location_id="TRK_01",
        primary_train_id="T2",
        secondary_train_id="T1",
        cause="Trailing train within 0.5km of lead train",
        predicted_impact="Cascading delay",
        recommendation="Harmonize speed",
        affected_resources=["TRK_01"],
        detected_at=datetime.now(timezone.utc)
    )
    
    resolution = ConflictResolver.resolve(conf, net)
    assert resolution["strategy"] == "SPEED_ADJUSTMENT"
    assert "target_train_id" in resolution["parameters"]
