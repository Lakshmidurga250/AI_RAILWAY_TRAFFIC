"""Unit and Continuous-Step Simulation Tests."""
from datetime import datetime, timezone
from simulation.engine.simulator import SimulationEngine
from simulation.network.loader import create_corridor_network
from simulation.trains.dynamics import TrainDynamics
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

def test_train_dynamics_kinematics():
    # Accelerating from 0 to 100 km/h
    v, dist, energy, regen = TrainDynamics.step_kinematics(
        current_speed_kmh=0.0,
        target_speed_kmh=100.0,
        max_acceleration_ms2=0.8,
        max_braking_ms2=1.0,
        dt_seconds=5.0,
        mass_tons=400.0
    )
    assert v > 0.0
    assert dist > 0.0
    assert energy > 0.0
    assert regen == 0.0

    # Braking from 100 to 0 km/h with regenerative energy recovery
    v_brake, dist_b, energy_b, regen_b = TrainDynamics.step_kinematics(
        current_speed_kmh=100.0,
        target_speed_kmh=0.0,
        max_acceleration_ms2=0.8,
        max_braking_ms2=1.0,
        dt_seconds=5.0,
        mass_tons=400.0
    )
    assert v_brake < 100.0
    assert regen_b > 0.0

def test_simulation_engine_step():
    engine = SimulationEngine(create_corridor_network())
    engine.initialize_default_traffic()
    assert len(engine.trains) >= 5

    init_time = engine.sim_time
    engine.step(dt_seconds=5.0)
    assert engine.sim_time > init_time

def test_event_bus_publish_subscribe():
    events_received = []
    
    def on_train_departed(event: SimEvent):
        events_received.append(event)

    event_bus.subscribe(EventType.TRAIN_DEPARTED, on_train_departed)
    
    test_event = SimEvent(
        event_type=EventType.TRAIN_DEPARTED,
        sim_time=datetime.now(timezone.utc),
        entity_id="TR_TEST",
        entity_type="TRAIN",
        payload={"station": "ST_SOUTH"}
    )
    event_bus.publish(test_event)

    assert len(events_received) >= 1
    assert events_received[-1].entity_id == "TR_TEST"
