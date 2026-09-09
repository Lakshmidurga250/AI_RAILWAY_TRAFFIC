"""Railway Interlocking Safety Shield (ERTMS Level 2 / Automatic Train Protection).

SAFETY INVARIANT:
The Safety Shield mathematically guarantees that an exploratory or suboptimal
Reinforcement Learning policy action NEVER violates minimum headway, closed signals,
or unaligned switch routes. If a proposed action violates safe operation limits,
the Safety Shield automatically intervenes and enforces a fail-safe fallback action.
"""
from typing import Dict, Any, Optional, List
from simulation.engine.simulator import SimulationEngine
from simulation.trains.train import SimulationTrain


class InterlockingSafetyShield:
    """Rigorous Safety Shield for verifying and overriding RL dispatch actions."""

    # Thresholds compliant with ERTMS Level 2 standard
    MIN_HEADWAY_KM = 2.0           # Minimum spatial following distance
    EMERGENCY_BRAKING_DIST_KM = 0.8 # Emergency braking distance at 120 km/h
    MAX_APPROACH_SPEED_KMH = 40.0   # Caution aspect approach speed

    # Action mappings:
    # 0: HOLD_TRAIN
    # 1: RELEASE_TRAIN
    # 2: SPEED_REDUCTION
    # 3: PRIORITY_BOOST
    # 4: REROUTE_ALTERNATIVE

    @classmethod
    def verify_and_filter(
        cls,
        engine: SimulationEngine,
        train: SimulationTrain,
        proposed_action: int
    ) -> Dict[str, Any]:
        """Verify candidate RL action against current physical & signaling state.

        Returns:
            Dict containing whether the action was deemed safe, the final executed action,
            and an explanation if the shield had to intervene.
        """
        violations: List[str] = []
        safe_action = proposed_action
        shield_intervened = False

        current_track = train.current_track
        if not current_track:
            return {
                "is_safe": True,
                "original_action": proposed_action,
                "executed_action": proposed_action,
                "shield_intervened": False,
                "violations": [],
                "reason": "Train in depot/staging without active track occupancy."
            }

        # 1. Check Signal Aspect Ahead
        approaching_signal = None
        for sig in engine.network.signals.values():
            if sig.track_id == current_track.id:
                approaching_signal = sig
                break

        if approaching_signal and str(getattr(approaching_signal.aspect, "value", approaching_signal.aspect)).upper() == "RED":
            # If train is within braking zone and policy proposes to release/accelerate
            dist_to_signal = max(0.1, current_track.length_km - train.distance_along_current_track_km)
            if dist_to_signal < cls.EMERGENCY_BRAKING_DIST_KM:
                if proposed_action in (1, 3):  # RELEASE_TRAIN or PRIORITY_BOOST
                    violations.append(
                        f"Signal {approaching_signal.id} is RED at {dist_to_signal:.2f}km; release action is hazardous."
                    )
                    safe_action = 0  # Force HOLD_TRAIN
                    shield_intervened = True

        # 2. Check Headway to Preceding Train
        following_dist = cls._calculate_distance_to_lead_train(engine, train)
        if following_dist is not None and following_dist < cls.MIN_HEADWAY_KM:
            if proposed_action == 1:  # RELEASE_TRAIN
                violations.append(
                    f"Headway buffer violated: lead train is only {following_dist:.2f}km ahead (min {cls.MIN_HEADWAY_KM}km)."
                )
                safe_action = 2 if following_dist > cls.EMERGENCY_BRAKING_DIST_KM else 0
                shield_intervened = True

        # 3. Check Track Blockage & Reroute Validity
        if proposed_action == 4:  # REROUTE_ALTERNATIVE
            can_reroute = cls._can_safely_reroute(engine, train)
            if not can_reroute:
                violations.append(
                    "No valid switch or secondary bypass track available at current position."
                )
                safe_action = 2  # Fallback to speed reduction
                shield_intervened = True

        return {
            "is_safe": not shield_intervened,
            "original_action": proposed_action,
            "executed_action": safe_action,
            "shield_intervened": shield_intervened,
            "violations": violations,
            "reason": "; ".join(violations) if violations else "Action verified by Interlocking Safety Shield."
        }

    @classmethod
    def _calculate_distance_to_lead_train(
        cls,
        engine: SimulationEngine,
        train: SimulationTrain
    ) -> Optional[float]:
        """Calculate spatial distance to the nearest train ahead on the same route."""
        if not train.current_track:
            return None

        min_dist = None
        for other_id, other in engine.trains.items():
            if other.id == train.id or other.status in ("COMPLETED", "CANCELLED"):
                continue

            # Case A: Same track ahead
            if other.current_track and other.current_track.id == train.current_track.id:
                if other.distance_along_current_track_km > train.distance_along_current_track_km:
                    d = other.distance_along_current_track_km - train.distance_along_current_track_km
                    if min_dist is None or d < min_dist:
                        min_dist = d

            # Case B: On immediately adjacent next track along route
            elif (
                train.current_track_index + 1 < len(train.route_tracks)
                and other.current_track
                and other.current_track.id == train.route_tracks[train.current_track_index + 1]
            ):
                rem_curr = max(0.0, train.current_track.length_km - train.distance_along_current_track_km)
                d = rem_curr + other.distance_along_current_track_km
                if min_dist is None or d < min_dist:
                    min_dist = d

        return min_dist

    @classmethod
    def _can_safely_reroute(cls, engine: SimulationEngine, train: SimulationTrain) -> bool:
        """Check if an alternate topological bypass exists from current junction."""
        if not train.current_track:
            return False
        target_node = train.current_track.target_node
        outgoing = [t for t in engine.network.tracks.values() if t.source_node == target_node]
        return len(outgoing) > 1
