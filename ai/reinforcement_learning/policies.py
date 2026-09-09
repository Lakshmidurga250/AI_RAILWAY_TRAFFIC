"""Reinforcement Learning Policies and Dispatch Agents."""
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class RuleBasedDispatcher:
    """Baseline heuristic dispatcher used for RL benchmarking."""

    @classmethod
    def select_action(cls, observation: np.ndarray, action_mask: Optional[np.ndarray] = None) -> int:
        """Heuristic rule: If active conflicts > 0, slow down or hold train; else release."""
        active_conflicts_norm = observation[36] if len(observation) > 36 else 0.0
        candidate = 1
        if active_conflicts_norm > 0.4:
            candidate = 0  # HOLD_TRAIN
        elif active_conflicts_norm > 0.15:
            candidate = 2  # SPEED_REDUCTION to 60 km/h

        if action_mask is not None and not action_mask[candidate]:
            # Choose fallback valid action
            for valid_a in [2, 0, 1, 3, 4]:
                if valid_a < len(action_mask) and action_mask[valid_a]:
                    return valid_a
        return candidate


class DQNAgent:
    """Deep Q-Network Agent with replay buffer, epsilon-greedy scheduling, and action masking."""

    def __init__(self, state_dim: int = 40, action_dim: int = 5, learning_rate: float = 0.001):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = learning_rate
        self.epsilon = 1.0
        self.epsilon_decay = 0.985
        self.epsilon_min = 0.05
        self.gamma = 0.95

        # Linear layer weights initialized with He-normal approximation
        np.random.seed(42)
        self.W1 = np.random.randn(state_dim, 64) * np.sqrt(2.0 / state_dim)
        self.b1 = np.zeros(64)
        self.W2 = np.random.randn(64, action_dim) * np.sqrt(2.0 / 64)
        self.b2 = np.zeros(action_dim)

    def forward(self, state: np.ndarray) -> np.ndarray:
        """Forward pass to compute Q(s, a)."""
        z1 = np.dot(state, self.W1) + self.b1
        a1 = np.maximum(0, z1)  # ReLU
        q_values = np.dot(a1, self.W2) + self.b2
        return q_values

    def select_action(
        self,
        state: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        evaluate: bool = False
    ) -> int:
        """Epsilon-greedy action selection with action mask constraint."""
        q_vals = self.forward(state)

        if action_mask is not None:
            # Mask invalid actions
            q_vals = np.copy(q_vals)
            q_vals[~action_mask] = -1e9

        if not evaluate and np.random.rand() < self.epsilon:
            if action_mask is not None and np.any(action_mask):
                valid_actions = np.where(action_mask)[0]
                return int(np.random.choice(valid_actions))
            return int(np.random.randint(self.action_dim))

        return int(np.argmax(q_vals))

    def update(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Single-step TD learning update."""
        q_current = self.forward(state)
        q_next = self.forward(next_state)
        target = reward if done else reward + self.gamma * np.max(q_next)

        # Compute gradient
        td_error = target - q_current[action]
        # Backprop through output layer
        z1 = np.dot(state, self.W1) + self.b1
        a1 = np.maximum(0, z1)

        grad_W2 = np.zeros_like(self.W2)
        grad_W2[:, action] = -td_error * a1
        self.W2 -= self.lr * grad_W2
        self.b2[action] -= self.lr * (-td_error)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


class PPOActorCritic:
    """Proximal Policy Optimization (PPO) Actor-Critic with Action Masking."""

    def __init__(
        self,
        state_dim: int = 40,
        action_dim: int = 5,
        lr_actor: float = 0.0003,
        lr_critic: float = 0.001,
        clip_ratio: float = 0.2
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.clip_ratio = clip_ratio
        self.lr_actor = lr_actor
        self.lr_critic = lr_critic

        # Actor: State -> Action Logits
        self.actor_W1 = np.random.randn(state_dim, 64) * np.sqrt(2.0 / state_dim)
        self.actor_b1 = np.zeros(64)
        self.actor_W2 = np.random.randn(64, action_dim) * np.sqrt(2.0 / 64)
        self.actor_b2 = np.zeros(action_dim)

        # Critic: State -> Scalar Value V(s)
        self.critic_W1 = np.random.randn(state_dim, 64) * np.sqrt(2.0 / state_dim)
        self.critic_b1 = np.zeros(64)
        self.critic_W2 = np.random.randn(64, 1) * np.sqrt(2.0 / 64)
        self.critic_b2 = np.zeros(1)

    def get_action_distribution(self, state: np.ndarray, action_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute softmax probability distribution over actions with masking support."""
        z1 = np.dot(state, self.actor_W1) + self.actor_b1
        a1 = np.maximum(0, z1)
        logits = np.dot(a1, self.actor_W2) + self.actor_b2

        if action_mask is not None:
            logits = np.copy(logits)
            logits[~action_mask] = -1e9

        # Stable softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        return probs

    def get_value(self, state: np.ndarray) -> float:
        """Compute state value estimate V(s)."""
        z1 = np.dot(state, self.critic_W1) + self.critic_b1
        a1 = np.maximum(0, z1)
        val = np.dot(a1, self.critic_W2) + self.critic_b2
        return float(val[0])

    def select_action(
        self,
        state: np.ndarray,
        action_mask: Optional[np.ndarray] = None,
        evaluate: bool = False
    ) -> Tuple[int, float, float]:
        """Select action via categorical sampling or greedy argmax."""
        probs = self.get_action_distribution(state, action_mask)
        if evaluate:
            action = int(np.argmax(probs))
        else:
            action = int(np.random.choice(self.action_dim, p=probs))

        log_prob = float(np.log(max(1e-8, probs[action])))
        val = self.get_value(state)
        return action, log_prob, val

    def update_policy(
        self,
        states: List[np.ndarray],
        actions: List[int],
        old_log_probs: List[float],
        returns: List[float],
        advantages: List[float]
    ) -> Dict[str, float]:
        """Execute PPO surrogate objective update step."""
        actor_losses = []
        critic_losses = []

        adv_arr = np.array(advantages)
        adv_norm = (adv_arr - np.mean(adv_arr)) / (np.std(adv_arr) + 1e-8) if len(adv_arr) > 1 else adv_arr

        for s, a, old_lp, ret, adv in zip(states, actions, old_log_probs, returns, adv_norm):
            probs = self.get_action_distribution(s)
            curr_lp = np.log(max(1e-8, probs[a]))
            ratio = np.exp(curr_lp - old_lp)

            # PPO Clipped Surrogate Loss
            surr1 = ratio * adv
            surr2 = np.clip(ratio, 1.0 - self.clip_ratio, 1.0 + self.clip_ratio) * adv
            actor_loss = -min(surr1, surr2)
            actor_losses.append(actor_loss)

            # Critic Squared Error Loss
            v_pred = self.get_value(s)
            critic_loss = 0.5 * (ret - v_pred) ** 2
            critic_losses.append(critic_loss)

            # Gradient update on critic
            z1_c = np.maximum(0, np.dot(s, self.critic_W1) + self.critic_b1)
            v_err = (v_pred - ret)
            self.critic_W2 -= self.lr_critic * (v_err * z1_c[:, None])
            self.critic_b2 -= self.lr_critic * v_err

        return {
            "mean_actor_loss": round(float(np.mean(actor_losses)), 4),
            "mean_critic_loss": round(float(np.mean(critic_losses)), 4)
        }
