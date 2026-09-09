"""Reinforcement Learning Environment and Benchmark Tests."""
from ai.reinforcement_learning.environment import RailwayGymEnv
from ai.reinforcement_learning.policies import DQNAgent, RuleBasedDispatcher

def test_gym_environment_initialization():
    env = RailwayGymEnv(max_steps=20)
    obs, info = env.reset()
    assert obs.shape == (env.obs_dim,)
    assert info["status"] == "INITIALIZED"

def test_gym_step_and_reward():
    env = RailwayGymEnv(max_steps=20)
    obs, _ = env.reset()
    
    # Step through all actions
    for action in range(env.action_dim):
        next_obs, reward, terminated, truncated, info = env.step(action)
        assert next_obs.shape == (env.obs_dim,)
        assert isinstance(reward, float)
        assert "action_taken" in info
        if terminated:
            break

def test_rule_based_baseline():
    env = RailwayGymEnv(max_steps=10)
    obs, _ = env.reset()
    action = RuleBasedDispatcher.select_action(obs)
    assert 0 <= action < env.action_dim
