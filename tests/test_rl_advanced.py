"""Tests for Advanced Reinforcement Learning, Action Masking, Safety Shield, and Multi-Agent Env."""
import uuid
import pytest
import numpy as np
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database import SessionLocal, engine, Base
from backend.repositories.rl_repository import RLRepository
from simulation.engine.simulator import sim_engine, SimulationEngine
from simulation.network.loader import create_corridor_network
from ai.reinforcement_learning.safety_shield import InterlockingSafetyShield
from ai.reinforcement_learning.action_masking import RailwayActionMasker
from ai.reinforcement_learning.multi_agent_env import MultiAgentRailwayGymEnv
from ai.reinforcement_learning.policies import PPOActorCritic, DQNAgent, RuleBasedDispatcher
from ai.reinforcement_learning.trainer import RLTrainer


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_safety_shield_signal_intervention():
    """Verify safety shield overrides dangerous release when signal is RED."""
    sim = SimulationEngine(create_corridor_network())
    sim.initialize_default_traffic()
    train = next(iter(sim.trains.values()))
    
    # Force signal on train track to RED
    if train.current_track:
        signal = None
        for s in sim.network.signals.values():
            if s.track_id == train.current_track.id:
                signal = s
                break
        if signal:
            from simulation.network.elements import SignalAspect
            signal.aspect = SignalAspect.RED
            train.distance_along_current_track_km = train.current_track.length_km - 0.2  # within 200m

            # Propose hazardous release
            res = InterlockingSafetyShield.verify_and_filter(sim, train, proposed_action=1)
            assert res["shield_intervened"] is True
            assert res["executed_action"] == 0  # Forced to HOLD
            assert len(res["violations"]) > 0


def test_action_masking():
    """Verify action masking blocks invalid commands."""
    sim = SimulationEngine(create_corridor_network())
    sim.initialize_default_traffic()
    train = next(iter(sim.trains.values()))

    mask = RailwayActionMasker.get_action_mask(sim, train)
    assert len(mask) == 5
    assert mask.dtype == bool
    # SPEED_REDUCTION (2) should be available
    assert bool(mask[2]) is True

    # Test logits masking
    logits = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    masked = RailwayActionMasker.apply_mask_to_logits(logits, np.array([True, False, True, True, False]))
    assert masked[1] == -1e9
    assert masked[4] == -1e9
    assert masked[0] == 1.0


def test_multi_agent_gym_env():
    """Test MultiAgentRailwayGymEnv step and reset transitions."""
    env = MultiAgentRailwayGymEnv(max_steps=5, max_agents=4)
    obs_dict, info_dict = env.reset()

    assert len(obs_dict) > 0
    first_agent = list(obs_dict.keys())[0]
    assert obs_dict[first_agent].shape == (env.AGENT_OBS_DIM,)
    assert "action_mask" in info_dict[first_agent]

    actions = {agent_id: 1 for agent_id in obs_dict.keys()}
    next_obs, rewards, terms, truncs, infos = env.step(actions)

    assert len(rewards) == len(obs_dict)
    assert isinstance(rewards[first_agent], float)
    assert first_agent in next_obs


def test_ppo_actor_critic():
    """Test PPO Actor-Critic policy inference and advantage update."""
    agent = PPOActorCritic(state_dim=12, action_dim=5)
    dummy_state = np.random.randn(12).astype(np.float32)

    action, log_p, val = agent.select_action(dummy_state)
    assert 0 <= action < 5
    assert isinstance(log_p, float)
    assert isinstance(val, float)

    # Perform policy update
    states = [dummy_state, dummy_state]
    actions = [action, 2]
    log_probs = [log_p, log_p]
    returns = [10.0, 5.0]
    advantages = [2.0, -1.0]

    loss_dict = agent.update_policy(states, actions, log_probs, returns, advantages)
    assert "mean_actor_loss" in loss_dict
    assert "mean_critic_loss" in loss_dict


def test_rl_repository_audit(db):
    """Test persistence of RL training and dispatch action logs."""
    repo = RLRepository(db)
    test_run_id = f"RL_TEST_RUN_{uuid.uuid4().hex[:8].upper()}"

    run = repo.record_training_run(
        run_id=test_run_id,
        algorithm="PROXIMAL_POLICY_OPTIMIZATION",
        episodes_trained=5,
        mean_episode_reward=42.5,
        shield_interventions_count=2,
        baseline_heuristic_reward=20.0,
        improvement_percentage=112.5,
        metrics={"test_metric": 1.0}
    )
    assert run.id == test_run_id
    assert run.improvement_percentage == 112.5

    # Record dispatch action
    log = repo.record_dispatch_action(
        train_id="TR_TEST_101",
        proposed_action="RELEASE_TRAIN",
        executed_action="HOLD_TRAIN",
        algorithm="PPO",
        shield_intervened=True,
        safety_violations=["Signal RED at approach"],
        reward=-5.0,
        explanation="Emergency hold enforced"
    )
    assert log.train_id == "TR_TEST_101"
    assert log.shield_intervened is True

    # Query recent
    recent_runs = repo.get_recent_training_runs(limit=10)
    assert any(r.id == test_run_id for r in recent_runs)


def test_rl_api_endpoints(client):
    """Test FastAPI endpoints for RL training, dispatch, and historical telemetry."""
    # 1. Dispatch action for active train
    active_train_id = next(iter(sim_engine.trains.keys()))
    dispatch_res = client.post("/optimization/rl/dispatch", json={
        "train_id": active_train_id,
        "algorithm": "DQN",
        "use_safety_shield": True
    })
    assert dispatch_res.status_code == 200
    data = dispatch_res.json()
    assert data["train_id"] == active_train_id
    assert "executed_action" in data
    assert "shield_intervened" in data
    assert len(data["action_mask"]) == 5

    # 2. Train quick episode
    train_res = client.post("/optimization/rl/train", json={
        "episodes": 2,
        "max_steps_per_episode": 5,
        "algorithm": "PPO",
        "use_action_masking": True
    })
    assert train_res.status_code == 200
    tdata = train_res.json()
    assert tdata["episodes_trained"] == 2
    assert "mean_episode_reward" in tdata

    # 3. Query training runs
    runs_res = client.get("/optimization/rl/runs?limit=5")
    assert runs_res.status_code == 200
    assert isinstance(runs_res.json(), list)
    assert len(runs_res.json()) > 0
