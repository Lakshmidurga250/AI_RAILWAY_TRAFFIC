"""Simulation CLI Demo Runner."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from simulation.engine.simulator import sim_engine
from ai.delay_prediction.predictor import delay_predictor
from ai.features.engineering import FeatureEngineer
from optimization.conflicts.resolver import conflict_resolver

def run_demo():
    print("=" * 70)
    print("  AI RAILWAY TRAFFIC OPTIMIZATION & DISCRETE SIMULATION DEMO")
    print("=" * 70)
    
    print(f"\n[*] Loaded Corridor Network: {len(sim_engine.network.stations)} Stations, {len(sim_engine.network.tracks)} Tracks")
    print(f"[*] Initial Active Fleet: {len(sim_engine.trains)} Trains")

    # Step simulation
    print("\n[*] Stepping simulation across 5 discrete time steps (10s each)...")
    for step_num in range(1, 6):
        sim_engine.step(dt_seconds=10.0)
        status = sim_engine.get_status_summary()
        print(f"  Step {step_num}: Sim Time: {status['current_sim_time']} | Avg Delay: {status['average_delay_minutes']}m | Punctuality: {status['punctuality_percentage']}%")

    # Pick a train and run AI Delay Prediction
    target_train = list(sim_engine.trains.values())[0]
    print(f"\n[*] Running Multi-Horizon Delay Prediction for Train {target_train.train_number} ({target_train.name})...")
    features = FeatureEngineer.extract_features_from_train(target_train)
    prediction = delay_predictor.predict(features, horizon_minutes=15, current_delay=target_train.current_delay_minutes)
    
    print(f"  > Forecasted Delay (15 min): {prediction['predicted_delay_minutes']} min")
    print(f"  > Confidence Score: {prediction['confidence'] * 100:.1f}%")
    print(f"  > Top Contributing Factors: {[f['factor'] for f in prediction['contributing_factors'][:3]]}")
    print(f"  > AI Narrative: {prediction['explanation']}")

    print("\n[+] Demo completed successfully. Web control center is available at http://localhost:8000")
    print("=" * 70)

if __name__ == "__main__":
    run_demo()
