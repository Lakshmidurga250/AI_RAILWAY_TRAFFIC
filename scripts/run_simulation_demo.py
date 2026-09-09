"""Interactive CLI Simulation Demo."""
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from simulation.engine.simulator import SimulationEngine
from simulation.network.loader import create_corridor_network
from simulation.engine.digital_twin import DigitalTwin

def run_demo():
    print("=" * 65)
    print("AI RAILWAY TRAFFIC DISCRETE-EVENT SIMULATION DEMO")
    print("=" * 65)

    engine = SimulationEngine(create_corridor_network())
    engine.initialize_default_traffic()
    dt = DigitalTwin(engine)

    print(f"[INIT] Loaded corridor network with {len(engine.network.stations)} stations, {len(engine.network.tracks)} tracks.")
    print(f"[INIT] Active fleet initialized: {len(engine.trains)} passenger & freight trains.")

    print("\nRunning 10 simulation ticks (dt=10s, accelerated 5x)...")
    for step in range(1, 11):
        engine.step(dt_seconds=10.0)
        snap = dt.get_live_snapshot()
        sim_stat = snap["simulation"]
        
        train_summaries = []
        for t in snap["trains"][:3]:
            train_summaries.append(f"{t['train_number']}: {t['speed_kmh']}km/h ({t['status']})")

        print(f"Step {step:2d} | Sim Time: {sim_stat['current_sim_time'][11:19]} | "
              f"Delays: {sim_stat['average_delay_minutes']}m | "
              f"Conflicts: {sim_stat['active_conflicts']} | "
              f"Energy: {sim_stat['total_energy_kwh']:.1f} kWh")
        print(f"        Fleet: {', '.join(train_summaries)}")
        time.sleep(0.3)

    print("\n[OK] Simulation demo successfully concluded.")

if __name__ == "__main__":
    run_demo()
