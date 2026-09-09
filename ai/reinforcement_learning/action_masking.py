"""Dynamic Action Masking for Railway Traffic Reinforcement Learning.

Action Masking restricts the action space at each decision step to strictly valid,
physically possible, and non-violating dispatch commands. This accelerates policy
convergence and guarantees that invalid transitions are never explored.
"""
from typing import List
import numpy as np
from simulation.engine.simulator import SimulationEngine
from simulation.trains.train import SimulationTrain
from ai.reinforcement_learning.safety_shield import InterlockingSafetyShield


class RailwayActionMasker:
    """Generates boolean action feasibility masks for dispatch reinforcement learning."""

    ACTION_COUNT = 5
    # 0: HOLD_TRAIN, 1: RELEASE_TRAIN, 2: SPEED_REDUCTION, 3: PRIORITY_BOOST, 4: REROUTE_ALTERNATIVE

    @classmethod
    def get_action_mask(cls, engine: SimulationEngine, train: SimulationTrain) -> np.ndarray:
        """Compute boolean validity mask for 5 candidate dispatch actions.

        Returns:
            np.ndarray of shape (5,) with dtype=bool, where True = valid, False = masked.
        """
        mask = np.ones(cls.ACTION_COUNT, dtype=bool)

        if not train.current_track or train.status in ("COMPLETED", "CANCELLED"):
            # If train is completed or not on track, only neutral action is allowed
            mask[:] = False
            mask[0] = True
            return mask

        # Check Action 1: RELEASE_TRAIN
        # Invalid if signal ahead is RED or distance to preceding train is within braking zone
        lead_dist = InterlockingSafetyShield._calculate_distance_to_lead_train(engine, train)
        if lead_dist is not None and lead_dist < InterlockingSafetyShield.MIN_HEADWAY_KM:
            mask[1] = False

        approaching_signal = None
        for sig in engine.network.signals.values():
            if sig.track_id == train.current_track.id:
                approaching_signal = sig
                break

        if approaching_signal and str(getattr(approaching_signal.aspect, "value", approaching_signal.aspect)).upper() == "RED":
            dist_to_sig = max(0.1, train.current_track.length_km - train.distance_along_current_track_km)
            if dist_to_sig < InterlockingSafetyShield.EMERGENCY_BRAKING_DIST_KM:
                mask[1] = False

        # Check Action 3: PRIORITY_BOOST
        # Invalid if already at maximum priority (10)
        if getattr(train, "priority", 5) >= 10:
            mask[3] = False

        # Check Action 4: REROUTE_ALTERNATIVE
        # Invalid if no secondary outgoing track exists at destination junction
        can_reroute = InterlockingSafetyShield._can_safely_reroute(engine, train)
        if not can_reroute:
            mask[4] = False

        # Ensure at least one action is always valid (fallback to HOLD or SPEED_REDUCTION)
        if not np.any(mask):
            mask[0] = True
            mask[2] = True

        return mask

    @classmethod
    def apply_mask_to_logits(cls, logits: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Set unmasked logits to a large negative value (-1e9) for softmax sampling."""
        masked_logits = np.copy(logits)
        masked_logits[~mask] = -1e9
        return masked_logits
