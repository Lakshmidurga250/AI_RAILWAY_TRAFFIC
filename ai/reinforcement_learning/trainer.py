"""Reinforcement Learning Trainer and Benchmark Evaluator."""
from typing import Dict, Any, List, Optional
import numpy as np
from ai.reinforcement_learning.environment import RailwayGymEnv
from ai.reinforcement_learning.policies import DQNAgent, PPOActorCritic, RuleBasedDispatcher
from ai.reinforcement_learning.action_masking import RailwayActionMasker
from ai.reinforcement_learning.safety_shield import InterlockingSafetyShield


class RLTrainer:
    """Trains RL dispatch agents (DQN & PPO) and benchmarks against heuristic baselines."""

    @classmethod
    def train_agent(
        cls,
        episodes: int = 15,
        max_steps_per_episode: int = 30,
        algorithm: str = "DQN",
        use_action_masking: bool = True
    ) -> Dict[str, Any]:
        """Train DQN or PPO agent on RailwayGymEnv with safety telemetry."""
        alg_upper = algorithm.upper()
        if alg_upper in ("PPO", "ACTOR_CRITIC"):
            return cls.train_ppo(episodes, max_steps_per_episode, use_action_masking)

        # Default DQN
        env = RailwayGymEnv(max_steps=max_steps_per_episode)
        agent = DQNAgent(state_dim=env.obs_dim, action_dim=env.action_dim)
        episode_rewards = []
        total_shield_interventions = 0

        for ep in range(episodes):
            state, _ = env.reset()
            total_reward = 0.0
            done = False

            while not done:
                # Compute mask if enabled
                target_train = max(env.engine.trains.values(), key=lambda t: t.current_delay_minutes) if env.engine.trains else None
                mask = RailwayActionMasker.get_action_mask(env.engine, target_train) if (use_action_masking and target_train) else None

                raw_action = agent.select_action(state, action_mask=mask)

                # Validate with Safety Shield
                if target_train:
                    shield_res = InterlockingSafetyShield.verify_and_filter(env.engine, target_train, raw_action)
                    action = shield_res["executed_action"]
                    if shield_res["shield_intervened"]:
                        total_shield_interventions += 1
                else:
                    action = raw_action

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
            "mean_episode_reward": round(float(np.mean(episode_rewards)), 2) if episode_rewards else 0.0,
            "shield_interventions_count": total_shield_interventions,
            "trained_agent_eval": eval_trained,
            "baseline_heuristic_eval": eval_baseline,
            "improvement_percentage": round(improvement_pct, 2),
            "final_epsilon": round(agent.epsilon, 3)
        }

    @classmethod
    def train_ppo(
        cls,
        episodes: int = 15,
        max_steps_per_episode: int = 30,
        use_action_masking: bool = True
    ) -> Dict[str, Any]:
        """Train PPO Actor-Critic agent on RailwayGymEnv."""
        env = RailwayGymEnv(max_steps=max_steps_per_episode)
        agent = PPOActorCritic(state_dim=env.obs_dim, action_dim=env.action_dim)
        episode_rewards = []
        total_shield_interventions = 0

        for ep in range(episodes):
            state, _ = env.reset()
            states, actions, log_probs, rewards, values = [], [], [], [], []
            done = False
            ep_reward = 0.0

            while not done:
                target_train = max(env.engine.trains.values(), key=lambda t: t.current_delay_minutes) if env.engine.trains else None
                mask = RailwayActionMasker.get_action_mask(env.engine, target_train) if (use_action_masking and target_train) else None

                raw_action, log_p, val = agent.select_action(state, action_mask=mask)

                if target_train:
                    shield_res = InterlockingSafetyShield.verify_and_filter(env.engine, target_train, raw_action)
                    action = shield_res["executed_action"]
                    if shield_res["shield_intervened"]:
                        total_shield_interventions += 1
                else:
                    action = raw_action

                next_state, reward, term, trunc, _ = env.step(action)
                done = term or trunc

                states.append(state)
                actions.append(action)
                log_probs.append(log_p)
                rewards.append(reward)
                values.append(val)

                state = next_state
                ep_reward += reward

            # Compute discounted returns and advantages
            gamma = 0.95
            returns = []
            discounted_r = 0.0
            for r in reversed(rewards):
                discounted_r = r + gamma * discounted_r
                returns.insert(0, discounted_r)

            advantages = [ret - v for ret, v in zip(returns, values)]
            agent.update_policy(states, actions, log_probs, returns, advantages)
            episode_rewards.append(round(ep_reward, 2))

        eval_trained = cls.evaluate_agent(agent, episodes=3)
        eval_baseline = cls.evaluate_baseline(episodes=3)

        improvement_pct = 0.0
        if eval_baseline["mean_reward"] != 0:
            improvement_pct = max(0.0, ((eval_trained["mean_reward"] - eval_baseline["mean_reward"]) / abs(eval_baseline["mean_reward"])) * 100.0)

        return {
            "algorithm": "PROXIMAL_POLICY_OPTIMIZATION",
            "episodes_trained": episodes,
            "training_rewards": episode_rewards,
            "mean_episode_reward": round(float(np.mean(episode_rewards)), 2) if episode_rewards else 0.0,
            "shield_interventions_count": total_shield_interventions,
            "trained_agent_eval": eval_trained,
            "baseline_heuristic_eval": eval_baseline,
            "improvement_percentage": round(improvement_pct, 2)
        }

    @classmethod
    def evaluate_agent(cls, agent: Any, episodes: int = 3) -> Dict[str, Any]:
        env = RailwayGymEnv(max_steps=25)
        rewards = []
        conflicts = []
        for _ in range(episodes):
            state, _ = env.reset()
            ep_reward = 0.0
            done = False
            while not done:
                if hasattr(agent, "select_action"):
                    # Works for both DQNAgent and PPOActorCritic
                    res = agent.select_action(state, evaluate=True)
                    action = res[0] if isinstance(res, tuple) else res
                else:
                    action = 1
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
