"""Property-Based Invariant Tests for AI Railway System.

Verifies graph reachability, simulation physics invariants, and scheduling constraints.
"""
import pytest
from datetime import datetime, timedelta, timezone
from simulation.network.loader import create_corridor_network
from simulation.trains.dynamics import TrainDynamics
from simulation.trains.train import SimulationTrain
from optimization.scheduling.scheduler import ScheduleOptimizer

def test_property_graph_distances_non_negative():
    """Invariant: All path distances between stations must be strictly positive and non-negative."""
    network = create_corridor_network()
    stations = list(network.stations.keys())
    for s1 in stations[:4]:
        for s2 in stations[4:8]:
            path = network.find_shortest_path(s1, s2)
            if path:
                tracks = network.path_to_tracks(path)
                total_km = sum(t.length_km for t in tracks)
                assert total_km > 0.0
                assert len(path) >= 2

def test_property_davis_resistance_monotonic():
    """Invariant: Davis train aerodynamic and rolling resistance strictly increases with speed."""
    prev_drag = 0.0
    for v in range(5, 200, 15):
        drag = TrainDynamics.calculate_resistance_force(mass_tons=400.0, speed_kmh=float(v))
        assert drag > prev_drag, f"Drag at {v} km/h ({drag}N) should exceed drag at lower speed ({prev_drag}N)"
        prev_drag = drag

def test_property_train_kinematics_speed_bounds():
    """Invariant: Train speed never exceeds max_speed_kmh and never falls below 0."""
    now = datetime.now(timezone.utc)
    network = create_corridor_network()
    train = SimulationTrain(
        train_id="TR_PROP_TEST",
        train_number="PROP-01",
        name="Invariant Runner",
        train_type="HIGH_SPEED",
        length_m=200.0,
        mass_tons=400.0,
        max_speed_kmh=180.0,
        acceleration_ms2=1.2,
        braking_ms2=1.5,
        passenger_capacity=500,
        current_passengers=300,
        priority=8,
        route_tracks=[],
        schedules=[]
    )
    # Accelerate hard for 200 seconds
    train.target_speed_kmh = 300.0  # Attempt target above max speed
    for _ in range(200):
        train.step(1.0, now, network.node_positions)
        assert 0.0 <= train.current_speed_kmh <= train.max_speed_kmh

    # Emergency brake for 200 seconds
    train.target_speed_kmh = 0.0
    for _ in range(200):
        train.step(1.0, now, network.node_positions)
        assert 0.0 <= train.current_speed_kmh <= train.max_speed_kmh
    assert train.current_speed_kmh == 0.0

def test_property_schedule_headway_constraint():
    """Invariant: Optimized timetable strictly enforces minimum headway separation on shared tracks."""
    network = create_corridor_network()
    now = datetime.now(timezone.utc)
    schedules = [
        {
            "train_id": f"TR_HEADWAY_{i}",
            "origin_station_id": "ST_CENTRAL",
            "destination_station_id": "ST_NORTH",
            "scheduled_departure": now + timedelta(seconds=i * 30),  # Conflicting simultaneous departures
            "priority": 5
        }
        for i in range(5)
    ]
    res = ScheduleOptimizer.optimize_timetable(network, schedules, start_time=now)
    timetable = res["timetable"]
    assert len(timetable) == 5

    # Verify spacing between consecutive departures
    for i in range(len(timetable) - 1):
        t1_dep = datetime.fromisoformat(timetable[i]["optimized_departure"])
        t2_dep = datetime.fromisoformat(timetable[i + 1]["optimized_departure"])
        headway_sec = (t2_dep - t1_dep).total_seconds()
        assert headway_sec >= ScheduleOptimizer.MIN_HEADWAY_SECONDS, (
            f"Headway {headway_sec}s between trains is less than safe minimum {ScheduleOptimizer.MIN_HEADWAY_SECONDS}s"
        )
