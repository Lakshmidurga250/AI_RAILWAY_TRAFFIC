"""Reinforcement Learning Policies and Dispatch Agents."""
import numpy as np
from typing import Dict, Any, List

class RuleBasedDispatcher:
    """Baseline heuristic dispatcher used for RL benchmarking."""
    
    @classmethod
    def select_action(cls, observation: np.ndarray) -> int:
        """Heuristic rule: If active conflicts > 0, slow down or hold train; else release."""
        active_conflicts_norm = observation[36]  # active_conflicts / 5.0
        if active_conflicts_norm > 0.15:
            return 2  # SPEED_REDUCTION to 60 km/h
        elif active_conflicts_norm > 0.4:
            return 0  # HOLD_TRAIN
        return 1  # RELEASE_TRAIN (proceed normally)

class DQNAgent:
    """Deep Q-Network Agent with replay buffer and Q-approximator."""

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

    def select_action(self, state: np.ndarray, evaluate: bool = False) -> int:
        """Epsilon-greedy action selection."""
        if not evaluate and np.random.rand() < self.epsilon:
            return int(np.random.randint(self.action_dim))
        q_vals = self.forward(state)
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
