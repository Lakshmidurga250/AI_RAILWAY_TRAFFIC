"""Reinforcement Learning Trainer and Benchmark Evaluator."""
from typing import Dict, Any, List
import numpy as np
from ai.reinforcement_learning.environment import RailwayGymEnv
from ai.reinforcement_learning.policies import DQNAgent, RuleBasedDispatcher

class RLTrainer:
    """Trains RL dispatch agent and compares results against heuristic baseline."""

    @classmethod
    def train_agent(cls, episodes: int = 15, max_steps_per_episode: int = 30) -> Dict[str, Any]:
        """Train DQN agent on RailwayGymEnv."""
        env = RailwayGymEnv(max_steps=max_steps_per_episode)
        agent = DQNAgent(state_dim=env.obs_dim, action_dim=env.action_dim)
        episode_rewards = []

        for ep in range(episodes):
            state, _ = env.reset()
            total_reward = 0.0
            done = False
            
            while not done:
                action = agent.select_action(state)
                next_state, reward, term, trunc, _ = env.step(action)
                done = term or trunc
                agent.update(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward

            episode_rewards.append(round(total_reward, 2))

        # Evaluate trained agent vs baseline
        eval_trained = cls.evaluate_agent(agent, episodes=3)
        eval_baseline = cls.evaluate_baseline(episodes=3)

        improvement_pct = 0.0
        if eval_baseline["mean_reward"] != 0:
            improvement_pct = max(0.0, ((eval_trained["mean_reward"] - eval_baseline["mean_reward"]) / abs(eval_baseline["mean_reward"])) * 100.0)

        return {
            "algorithm": "DEEP_Q_NETWORK",
            "episodes_trained": episodes,
            "training_rewards": episode_rewards,
            "trained_agent_eval": eval_trained,
            "baseline_heuristic_eval": eval_baseline,
            "improvement_percentage": round(improvement_pct, 2),
            "final_epsilon": round(agent.epsilon, 3)
        }

    @classmethod
    def evaluate_agent(cls, agent: DQNAgent, episodes: int = 3) -> Dict[str, Any]:
        env = RailwayGymEnv(max_steps=25)
        rewards = []
        conflicts = []
        for _ in range(episodes):
            state, _ = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = agent.select_action(state, evaluate=True)
                state, reward, term, trunc, info = env.step(action)
                done = term or trunc
                ep_reward += reward
            rewards.append(ep_reward)
            conflicts.append(info.get("active_conflicts", 0))

        return {
            "mean_reward": round(float(np.mean(rewards)), 2),
            "mean_active_conflicts": round(float(np.mean(conflicts)), 2)
        }

    @classmethod
    def evaluate_baseline(cls, episodes: int = 3) -> Dict[str, Any]:
        env = RailwayGymEnv(max_steps=25)
        rewards = []
        conflicts = []
        for _ in range(episodes):
            state, _ = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                action = RuleBasedDispatcher.select_action(state)
                state, reward, term, trunc, info = env.step(action)
                done = term or trunc
                ep_reward += reward
            rewards.append(ep_reward)
            conflicts.append(info.get("active_conflicts", 0))

        return {
            "mean_reward": round(float(np.mean(rewards)), 2),
            "mean_active_conflicts": round(float(np.mean(conflicts)), 2)
        }
