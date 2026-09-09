"""AI Model Training and Evaluation Script."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai.delay_prediction.predictor import DelayPredictor
from ai.reinforcement_learning.trainer import RLTrainer
from ai.data.synthetic import synthetic_generator

def main():
    print("=" * 65)
    print("  TRAINING RAILWAY AI MODELS & BENCHMARKS")
    print("=" * 65)

    # 1. Train Delay Predictor
    print("\n[1/2] Generating synthetic operational dataset & training Gradient Boosting Delay Predictor...")
    df = synthetic_generator.generate_delay_training_dataset(num_samples=1500)
    predictor = DelayPredictor()
    predictor.train_models(df)
    
    print("  Validation Metrics across Horizons:")
    for h, m in predictor.metrics.items():
        print(f"    Horizon {h:2d}m -> MAE: {m['MAE']:.3f}m | RMSE: {m['RMSE']:.3f}m | R2: {m['R2']:.3f}")

    # 2. Train RL DQN Agent
    print("\n[2/2] Training Reinforcement Learning DQN Dispatch Policy (10 episodes)...")
    rl_results = RLTrainer.train_agent(episodes=10, max_steps_per_episode=25)
    print(f"  Trained Mean Reward: {rl_results['trained_agent_eval']['mean_reward']}")
    print(f"  Baseline Heuristic Reward: {rl_results['baseline_heuristic_eval']['mean_reward']}")
    print(f"  Improvement vs Heuristic: +{rl_results['improvement_percentage']:.1f}%")

    print("\n[+] All models trained and validated successfully.")
    print("=" * 65)

if __name__ == "__main__":
    main()
