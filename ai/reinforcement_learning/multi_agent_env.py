"""Multi-Agent Decentralized Railway Traffic Gymnasium Environment (MARL).

In this environment, each active train in the corridor is modeled as an independent
cooperative dispatch agent. Agents observe local track/signal conditions and coordinate
joint actions to maximize corridor throughput and minimize collective delays without deadlock.
"""
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from simulation.network.loader import create_corridor_network
from simulation.engine.simulator import SimulationEngine
from simulation.trains.train import SimulationTrain
from ai.reinforcement_learning.safety_shield import InterlockingSafetyShield
from ai.reinforcement_learning.action_masking import RailwayActionMasker


class MultiAgentRailwayGymEnv:
    """Decentralized Multi-Agent Environment for Cooperative Train Dispatching."""

    # Local observation space dimension per agent = 12
    # [speed_norm, delay_norm, track_idx_norm, dist_ratio, priority_norm, is_dwelling,
    #  lead_dist_norm, signal_ahead_red, active_conflicts_norm, system_avg_delay,
    #  track_occupancy_ratio, energy_norm]
    AGENT_OBS_DIM = 12
    ACTION_DIM = 5

    def __init__(self, max_steps: int = 60, max_agents: int = 6):
        self.max_steps = max_steps
        self.max_agents = max_agents
        self.current_step = 0
        self.engine = SimulationEngine(create_corridor_network())
        self.engine.initialize_default_traffic()
        self.agents: List[str] = []

    def reset(self, seed: Optional[int] = None) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """Reset environment and return observations for all active train agents."""
        self.current_step = 0
        self.engine = SimulationEngine(create_corridor_network())
        self.engine.initialize_default_traffic()
        self.agents = [t_id for t_id in list(self.engine.trains.keys())[:self.max_agents]]

        observations = {agent_id: self._get_agent_observation(agent_id) for agent_id in self.agents}
        infos = {
            agent_id: {
                "action_mask": RailwayActionMasker.get_action_mask(self.engine, self.engine.trains[agent_id])
            }
            for agent_id in self.agents
        }
        return observations, infos

    def _get_agent_observation(self, agent_id: str) -> np.ndarray:
        """Construct localized feature observation for a specific train agent."""
        if agent_id not in self.engine.trains:
            return np.zeros(self.AGENT_OBS_DIM, dtype=np.float32)

        train = self.engine.trains[agent_id]
        trk_len = train.current_track.length_km if train.current_track else 10.0
        dist_ratio = min(1.0, max(0.0, train.distance_along_current_track_km / max(0.1, trk_len)))

        # Preceding train distance
        lead_dist = InterlockingSafetyShield._calculate_distance_to_lead_train(self.engine, train)
        lead_norm = min(1.0, lead_dist / 10.0) if lead_dist is not None else 1.0

        # Signal state ahead
        signal_red = 0.0
        if train.current_track:
            for sig in self.engine.network.signals.values():
                if sig.track_id == train.current_track.id and str(getattr(sig.aspect, "value", sig.aspect)).upper() == "RED":
                    signal_red = 1.0
                    break

        # Corridor system metrics
        active_conflicts = len(self.engine.conflict_detector.active_conflicts)
        delays = [t.current_delay_minutes for t in self.engine.trains.values()]
        avg_delay = (sum(delays) / len(delays)) if delays else 0.0
        occupied_tracks = sum(1 for trk in self.engine.network.tracks.values() if len(trk.current_train_ids) > 0)
        track_occ_ratio = occupied_tracks / max(1, len(self.engine.network.tracks))

        obs = np.array([
            train.current_speed_kmh / 200.0,
            min(1.0, train.current_delay_minutes / 30.0),
            float(train.current_track_index) / 10.0,
            dist_ratio,
            float(train.priority) / 10.0,
            1.0 if train.status == "DWELLING" else 0.0,
            lead_norm,
            signal_red,
            min(1.0, active_conflicts / 5.0),
            min(1.0, avg_delay / 20.0),
            track_occ_ratio,
            min(1.0, self.engine.total_energy_kwh / 10000.0)
        ], dtype=np.float32)

        return obs

    def step(
        self,
        actions: Dict[str, int]
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, float], Dict[str, bool], Dict[str, bool], Dict[str, Any]]:
        """Apply joint multi-agent actions, verify through safety shield, advance simulation."""
        self.current_step += 1
        shield_interventions: Dict[str, bool] = {}

        # 1. Apply verified action for each agent
        for agent_id, proposed_action in actions.items():
            if agent_id in self.engine.trains:
                train = self.engine.trains[agent_id]
                # Pass through safety shield
                verification = InterlockingSafetyShield.verify_and_filter(self.engine, train, proposed_action)
                executed_action = verification["executed_action"]
                shield_interventions[agent_id] = verification["shield_intervened"]

                if executed_action == 0:    # HOLD
                    train.target_speed_kmh = 0.0
                elif executed_action == 1:  # RELEASE
                    train.target_speed_kmh = train.max_speed_kmh
                elif executed_action == 2:  # SLOW
                    train.target_speed_kmh = 60.0
                elif executed_action == 3:  # PRIORITY
                    train.priority = min(10, train.priority + 1)
                elif executed_action == 4:  # REROUTE
                    train.target_speed_kmh = 50.0

        # 2. Step simulation
        self.engine.step(dt_seconds=10.0)

        # 3. Compute rewards, terminations, and next observations
        observations: Dict[str, np.ndarray] = {}
        rewards: Dict[str, float] = {}
        terminations: Dict[str, bool] = {}
        truncations: Dict[str, bool] = {}
        infos: Dict[str, Any] = {}

        all_completed = all(t.status in ("COMPLETED", "CANCELLED") for t in self.engine.trains.values())
        system_conflicts = len(self.engine.conflict_detector.active_conflicts)

        for agent_id in self.agents:
            if agent_id in self.engine.trains:
                train = self.engine.trains[agent_id]
                is_done = train.status in ("COMPLETED", "CANCELLED")
                terminations[agent_id] = is_done or all_completed or (self.current_step >= self.max_steps)
                truncations[agent_id] = False

                # Reward composition:
                # - Punctuality reward: penalize delay
                # - Safety penalty: penalize active conflict involving this train
                # - Throughput bonus: if completed
                # - Shield intervention penalty: -5 to encourage compliant policy learning
                reward = -0.5 * train.current_delay_minutes
                if any(train.id in (c.primary_train_id, c.secondary_train_id) for c in self.engine.conflict_detector.active_conflicts.values()):
                    reward -= 25.0
                if train.status == "COMPLETED":
                    reward += 50.0
                if shield_interventions.get(agent_id, False):
                    reward -= 5.0

                rewards[agent_id] = round(float(reward), 2)
                observations[agent_id] = self._get_agent_observation(agent_id)
                infos[agent_id] = {
                    "action_mask": RailwayActionMasker.get_action_mask(self.engine, train),
                    "shield_intervened": shield_interventions.get(agent_id, False),
                    "delay_minutes": train.current_delay_minutes,
                    "status": train.status
                }

        return observations, rewards, terminations, truncations, infos
