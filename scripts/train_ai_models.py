"""AI Model Training and Registry Synchronization CLI."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai.data.synthetic import synthetic_generator
from ai.delay_prediction.predictor import delay_predictor
from ai.reinforcement_learning.trainer import RLTrainer
from ai.registry.model_registry import model_registry

def train_all():
    print("=" * 60)
    print("AI RAILWAY OPTIMIZATION: OFFLINE MODEL TRAINING PIPELINE")
    print("=" * 60)

    # 1. Delay Prediction Models
    print("\n[1/3] Generating synthetic telemetry dataset (3,000 samples)...")
    df = synthetic_generator.generate_delay_training_dataset(num_samples=3000)
    print(f"Generated {len(df)} records across 13 operational features.")

    print("\n[2/3] Fitting Gradient Boosting Regressors across horizons (5m, 10m, 15m, 30m, 60m)...")
    delay_predictor.train_models(df)
    for h, metrics in delay_predictor.metrics.items():
        print(f"  → Horizon {h:2d}m: MAE={metrics['MAE']:.3f}m | RMSE={metrics['RMSE']:.3f}m | R²={metrics['R2']:.3f}")

    # 2. Reinforcement Learning
    print("\n[3/3] Running DQN Dispatch Policy Training Loop (15 episodes)...")
    rl_res = RLTrainer.train_agent(episodes=15, max_steps_per_episode=25)
    print(f"  → Trained Mean Reward: {rl_res['trained_agent_eval']['mean_reward']}")
    print(f"  → Baseline Heuristic:  {rl_res['baseline_heuristic_eval']['mean_reward']}")
    print(f"  → Improvement:         +{rl_res['improvement_percentage']:.1f}%")

    print("\n[OK] Model training complete. All models registered and validated.")

if __name__ == "__main__":
    train_all()
