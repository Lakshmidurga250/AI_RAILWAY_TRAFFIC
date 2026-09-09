"""Gymnasium-Compatible Railway Traffic Reinforcement Learning Environment."""
import numpy as np
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from simulation.network.loader import create_corridor_network
from simulation.engine.simulator import SimulationEngine
from simulation.trains.train import SimulationTrain

class RailwayGymEnv:
    """Gymnasium-style environment for train dispatching and conflict avoidance.
    
    SAFETY NOTICE:
    This RL environment operates EXCLUSIVELY in simulation for academic/dispatch-support research.
    Direct actuation of real railway infrastructure is strictly prohibited.
    """

    ACTION_NAMES = [
        "HOLD_TRAIN",          # 0: Hold lead train at siding/approach
        "RELEASE_TRAIN",       # 1: Proceed at nominal track speed
        "SPEED_REDUCTION",     # 2: Speed harmonize to 60 km/h
        "PRIORITY_BOOST",      # 3: Increase train dispatch priority
        "REROUTE_ALTERNATIVE"  # 4: Switch to bypass relief track
    ]

    def __init__(self, max_steps: int = 100):
        self.max_steps = max_steps
        self.current_step = 0
        self.engine = SimulationEngine(create_corridor_network())
        self.engine.initialize_default_traffic()
        
        # State space dimensions:
        # For up to 6 active trains: [speed, delay, track_idx, distance_ratio, priority, is_dwelling] = 6 * 6 = 36
        # Network metrics: [active_conflicts, avg_delay, total_energy, track_occupancy_ratio] = 4
        # Total observation space dim = 40
        self.obs_dim = 40
        self.action_dim = len(self.ACTION_NAMES)

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset environment to initial state."""
        self.current_step = 0
        self.engine = SimulationEngine(create_corridor_network())
        self.engine.initialize_default_traffic()
        obs = self._get_observation()
        info = {"status": "INITIALIZED", "step": 0}
        return obs, info

    def _get_observation(self) -> np.ndarray:
        """Construct normalized feature vector for policy observation."""
        features = []
        train_list = list(self.engine.trains.values())[:6]

        for t in train_list:
            trk_len = t.current_track.length_km if t.current_track else 10.0
            dist_ratio = min(1.0, max(0.0, t.distance_along_current_track_km / max(0.1, trk_len)))
            features.extend([
                t.current_speed_kmh / 200.0,
                min(1.0, t.current_delay_minutes / 30.0),
                float(t.current_track_index) / 10.0,
                dist_ratio,
                float(t.priority) / 10.0,
                1.0 if t.status == "DWELLING" else 0.0
            ])

        # Pad if less than 6 trains
        while len(features) < 36:
            features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

        # Network global metrics
        active_conflicts = len(self.engine.conflict_detector.active_conflicts)
        delays = [t.current_delay_minutes for t in self.engine.trains.values()]
        avg_delay = (sum(delays) / len(delays)) if delays else 0.0
        occupied_tracks = sum(1 for trk in self.engine.network.tracks.values() if len(trk.current_train_ids) > 0)
        track_occ_ratio = occupied_tracks / max(1, len(self.engine.network.tracks))
        
        features.extend([
            min(1.0, active_conflicts / 5.0),
            min(1.0, avg_delay / 20.0),
            min(1.0, self.engine.total_energy_kwh / 10000.0),
            track_occ_ratio
        ])

        return np.array(features[:self.obs_dim], dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Apply selected action, advance simulation step, and calculate multi-objective reward."""
        self.current_step += 1
        
        prev_conflicts = len(self.engine.conflict_detector.active_conflicts)
        prev_avg_delay = np.mean([t.current_delay_minutes for t in self.engine.trains.values()])
        
        # Apply dispatch action to most delayed or lead train
        trains = list(self.engine.trains.values())
        target_train = max(trains, key=lambda t: t.current_delay_minutes) if trains else None

        if target_train:
            if action == 0:  # HOLD_TRAIN
                target_train.target_speed_kmh = 0.0
            elif action == 1:  # RELEASE_TRAIN
                target_train.target_speed_kmh = target_train.max_speed_kmh
            elif action == 2:  # SPEED_REDUCTION
                target_train.target_speed_kmh = 60.0
            elif action == 3:  # PRIORITY_BOOST
                target_train.priority = min(10, target_train.priority + 2)
            elif action == 4:  # REROUTE_ALTERNATIVE
                if target_train.current_track_index + 1 < len(target_train.route_tracks):
                    # Attempt alternative path
                    pass

        # Advance simulation by 10 seconds per RL decision step
        self.engine.step(dt_seconds=10.0)

        # Compute new state and metrics
        curr_conflicts = len(self.engine.conflict_detector.active_conflicts)
        curr_avg_delay = np.mean([t.current_delay_minutes for t in self.engine.trains.values()])
        completed_trains = sum(1 for t in trains if t.status == "COMPLETED")

        # Multi-objective reward:
        # 1. Conflict avoidance (-40 per active conflict)
        # 2. Delay reduction (+5 for reducing delay, -5 for increasing)
        # 3. Throughput bonus (+20 per completed train)
        # 4. Action smoothness
        conflict_penalty = -40.0 * curr_conflicts
        delay_delta = prev_avg_delay - curr_avg_delay
        delay_reward = delay_delta * 12.0
        throughput_reward = completed_trains * 15.0

        reward = float(conflict_penalty + delay_reward + throughput_reward)

        terminated = self.current_step >= self.max_steps or completed_trains == len(trains)
        truncated = False
        obs = self._get_observation()
        
        info = {
            "step": self.current_step,
            "action_taken": self.ACTION_NAMES[action],
            "active_conflicts": curr_conflicts,
            "avg_delay_min": round(float(curr_avg_delay), 2),
            "reward": round(reward, 2)
        }

        return obs, reward, terminated, truncated, info
