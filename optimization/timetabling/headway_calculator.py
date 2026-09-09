"""
Headway Calculator for Railway Timetabling.

Implements:
- Minimum headway computation (blocking time theory)
- Blocking time stairway calculation
- Signalling system headway (fixed block, moving block)
- Station approach headway
- Platform occupation time
- Overlap headway
- Headway sensitivity analysis
- Grade-of-automation influence
- ETCS level headway comparison (L1, L2, L3)
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SignallingSystem(Enum):
    FIXED_BLOCK_2ASPECT = "FB2"          # 2-aspect fixed block
    FIXED_BLOCK_3ASPECT = "FB3"          # 3-aspect fixed block
    FIXED_BLOCK_4ASPECT = "FB4"          # 4-aspect fixed block
    MOVING_BLOCK = "MB"                  # Moving block (ETCS L3)
    ETCS_LEVEL_1 = "ETCS_L1"
    ETCS_LEVEL_2 = "ETCS_L2"
    ETCS_LEVEL_3 = "ETCS_L3"


class TrackType(Enum):
    SINGLE_TRACK = "single"
    DOUBLE_TRACK = "double"
    MULTI_TRACK = "multi"
    YARD = "yard"


@dataclass
class BlockSection:
    """A signal block section between two signals."""
    section_id: str
    length_m: float
    gradient_permille: float = 0.0
    speed_limit_kmh: float = 160.0
    signal_distance_m: float = 1000.0   # Distance from signal to block entry
    clearing_point_m: float = 50.0      # Distance past exit signal to clearing point


@dataclass
class HeadwayResult:
    """Result of headway computation."""
    section_id: str
    signalling_system: SignallingSystem
    min_headway_s: float
    min_headway_min: float
    components: Dict[str, float] = field(default_factory=dict)

    # Breakdown
    braking_time_s: float = 0.0
    clearing_time_s: float = 0.0
    signal_spacing_time_s: float = 0.0
    reaction_time_s: float = 0.0
    dwell_time_s: float = 0.0
    overlap_time_s: float = 0.0

    # Sensitivity
    headway_at_10pct_delay: Optional[float] = None
    headway_at_max_load: Optional[float] = None

    def __repr__(self) -> str:
        return (f"HeadwayResult({self.section_id!r}, "
                f"{self.min_headway_min:.1f} min, "
                f"system={self.signalling_system.value})")


class HeadwayCalculator:
    """
    Implements the UIC 406 blocking time theory for minimum headway computation.

    The blocking time stairway method:
    1. Train approaches signal at end of block
    2. Signal changes to proceed at t0
    3. Train enters block at t1 = t0 + approach_time
    4. Train clears block at t2 = t1 + traversal_time
    5. Next train can enter at t3 = t2 + clearing_time + overlap
    6. Minimum headway H = t3 - t0
    """

    # Physical constants
    G = 9.81  # m/s^2

    # Driver reaction times (seconds)
    REACTION_TIMES = {
        SignallingSystem.FIXED_BLOCK_2ASPECT: 6.0,
        SignallingSystem.FIXED_BLOCK_3ASPECT: 5.0,
        SignallingSystem.FIXED_BLOCK_4ASPECT: 4.0,
        SignallingSystem.MOVING_BLOCK: 0.5,
        SignallingSystem.ETCS_LEVEL_1: 3.0,
        SignallingSystem.ETCS_LEVEL_2: 2.5,
        SignallingSystem.ETCS_LEVEL_3: 1.0,
    }

    # Deceleration rates (m/s^2)
    DECELERATION_RATES = {
        "EMU": 0.9,
        "DMU": 0.8,
        "Locomotive_Hauled": 0.7,
        "High_Speed": 0.85,
        "Freight": 0.5,
    }

    def __init__(self, default_signalling: SignallingSystem = SignallingSystem.FIXED_BLOCK_4ASPECT) -> None:
        self.default_signalling = default_signalling
        self._cached_results: Dict[str, HeadwayResult] = {}

    def compute_braking_distance(self, speed_kmh: float, deceleration_ms2: float,
                                  gradient_permille: float = 0.0) -> float:
        """
        Compute braking distance (m) using kinematic formula with grade correction.
        v^2 = 2 * a * d  =>  d = v^2 / (2a)
        """
        v_ms = speed_kmh / 3.6
        effective_decel = deceleration_ms2 + self.G * gradient_permille / 1000.0
        if effective_decel <= 0:
            return float('inf')
        return v_ms ** 2 / (2 * effective_decel)

    def compute_braking_time(self, speed_kmh: float, deceleration_ms2: float) -> float:
        """Compute braking time (s): t = v / a"""
        v_ms = speed_kmh / 3.6
        return v_ms / deceleration_ms2

    def compute_traversal_time(self, length_m: float, speed_kmh: float,
                                deceleration_ms2: float, gradient_permille: float = 0.0) -> float:
        """
        Time for train to traverse a block section.
        Accounts for entry at speed and exit deceleration.
        """
        v_entry_ms = speed_kmh / 3.6
        traversal_time = length_m / v_entry_ms
        # Add time for grade effects
        grade_factor = 1.0 + abs(gradient_permille) / 1000.0 * 0.1
        return traversal_time * grade_factor

    def compute_minimum_headway_fixed_block(
            self,
            block: BlockSection,
            train_type: str = "EMU",
            signalling: Optional[SignallingSystem] = None,
            station_dwell_s: float = 0.0,
    ) -> HeadwayResult:
        """
        Compute minimum headway for fixed-block signalling using blocking time theory.

        H = t_reaction + t_signal_approach + t_braking + t_clearing + t_dwell + t_overlap
        """
        sys = signalling or self.default_signalling
        decel = self.DECELERATION_RATES.get(train_type, 0.9)
        reaction_t = self.REACTION_TIMES.get(sys, 5.0)

        speed_ms = block.speed_limit_kmh / 3.6

        # Braking time
        braking_t = self.compute_braking_time(block.speed_limit_kmh, decel)

        # Train traversal time through the block
        traversal_t = self.compute_traversal_time(
            block.length_m, block.speed_limit_kmh, decel, block.gradient_permille)

        # Clearing time (train tail past clearing point)
        clearing_t = block.clearing_point_m / speed_ms if speed_ms > 0 else 0

        # Signal spacing time (time to travel from previous signal to block entry)
        signal_spacing_t = block.signal_distance_m / speed_ms if speed_ms > 0 else 0

        # Overlap time (safety distance beyond exit signal)
        overlap_length_m = min(200.0, block.length_m * 0.2)
        overlap_t = overlap_length_m / speed_ms if speed_ms > 0 else 0

        # Total minimum headway
        total_headway_s = (reaction_t + signal_spacing_t + braking_t +
                           traversal_t + clearing_t + station_dwell_s + overlap_t)

        result = HeadwayResult(
            section_id=block.section_id,
            signalling_system=sys,
            min_headway_s=total_headway_s,
            min_headway_min=total_headway_s / 60.0,
            braking_time_s=braking_t,
            clearing_time_s=clearing_t,
            signal_spacing_time_s=signal_spacing_t,
            reaction_time_s=reaction_t,
            dwell_time_s=station_dwell_s,
            overlap_time_s=overlap_t,
            components={
                "reaction_time_s": reaction_t,
                "signal_spacing_time_s": signal_spacing_t,
                "braking_time_s": braking_t,
                "traversal_time_s": traversal_t,
                "clearing_time_s": clearing_t,
                "dwell_time_s": station_dwell_s,
                "overlap_time_s": overlap_t,
            }
        )

        # Sensitivity analysis
        result.headway_at_10pct_delay = total_headway_s * 1.1
        result.headway_at_max_load = total_headway_s + station_dwell_s * 0.5

        self._cached_results[block.section_id] = result
        return result

    def compute_minimum_headway_moving_block(
            self,
            block: BlockSection,
            train_length_m: float = 200.0,
            safety_margin_m: float = 50.0,
            train_type: str = "EMU",
    ) -> HeadwayResult:
        """
        Compute minimum headway for moving block (ETCS Level 3).
        The headway is the physical train separation required.
        H = (braking_distance + train_length + safety_margin) / speed
        """
        decel = self.DECELERATION_RATES.get(train_type, 0.9)
        braking_dist = self.compute_braking_distance(block.speed_limit_kmh, decel,
                                                      block.gradient_permille)
        speed_ms = block.speed_limit_kmh / 3.6

        separation_m = braking_dist + train_length_m + safety_margin_m
        headway_s = separation_m / speed_ms if speed_ms > 0 else 0.0

        return HeadwayResult(
            section_id=block.section_id,
            signalling_system=SignallingSystem.MOVING_BLOCK,
            min_headway_s=headway_s,
            min_headway_min=headway_s / 60.0,
            braking_time_s=self.compute_braking_time(block.speed_limit_kmh, decel),
            components={
                "braking_distance_m": braking_dist,
                "train_length_m": train_length_m,
                "safety_margin_m": safety_margin_m,
                "total_separation_m": separation_m,
            }
        )

    def compare_signalling_systems(
            self, block: BlockSection, train_type: str = "EMU"
    ) -> Dict[str, HeadwayResult]:
        """Compare headways for all signalling systems."""
        results = {}
        for sys in SignallingSystem:
            if sys == SignallingSystem.MOVING_BLOCK or sys == SignallingSystem.ETCS_LEVEL_3:
                results[sys.value] = self.compute_minimum_headway_moving_block(
                    block, train_type=train_type)
            else:
                results[sys.value] = self.compute_minimum_headway_fixed_block(
                    block, train_type=train_type, signalling=sys)
        return results

    def compute_line_capacity(self, blocks: List[BlockSection],
                               signalling: Optional[SignallingSystem] = None,
                               train_mix: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        UIC 406 capacity computation.
        Infrastructure capacity = 1440 min / min_headway.
        Practical capacity = infrastructure_capacity * compression_factor.
        """
        if not blocks:
            return {"error": "No blocks provided"}

        sys = signalling or self.default_signalling
        headways = [
            self.compute_minimum_headway_fixed_block(b, signalling=sys)
            for b in blocks
        ]

        # Bottleneck headway (maximum minimum headway)
        bottleneck = max(headways, key=lambda h: h.min_headway_s)
        infrastructure_capacity = int(1440 / (bottleneck.min_headway_min + 0.001))

        # Train mix heterogeneity penalty
        mix_factor = 1.0
        if train_mix:
            # Mixed traffic reduces capacity
            n_categories = len(train_mix)
            mix_factor = 1.0 - (n_categories - 1) * 0.05

        # UIC compression factor (ratio of ideal to practical)
        compression_factor = 0.75  # Typical 75% practical capacity
        practical_capacity = int(infrastructure_capacity * compression_factor * mix_factor)

        return {
            "signalling_system": sys.value,
            "num_blocks": len(blocks),
            "bottleneck_block": bottleneck.section_id,
            "bottleneck_headway_min": round(bottleneck.min_headway_min, 2),
            "infrastructure_capacity_trains_per_day": infrastructure_capacity,
            "compression_factor": compression_factor,
            "mix_factor": round(mix_factor, 3),
            "practical_capacity_trains_per_day": practical_capacity,
            "all_headways": [
                {"block": h.section_id, "headway_min": round(h.min_headway_min, 2)}
                for h in headways
            ],
        }

    def blocking_time_stairway(self, block: BlockSection,
                                train_type: str = "EMU") -> Dict[str, Any]:
        """
        Generate the blocking time stairway diagram data.
        Returns time-position data for visualization.
        """
        result = self.compute_minimum_headway_fixed_block(block, train_type)

        # Build stairway points (simplified linear model)
        events = [
            {"event": "signal_approach_start", "time_s": 0, "position_m": -block.signal_distance_m},
            {"event": "signal_clears",          "time_s": result.reaction_time_s, "position_m": -block.signal_distance_m},
            {"event": "train_enters_block",     "time_s": result.reaction_time_s + result.signal_spacing_time_s, "position_m": 0},
            {"event": "train_exits_block",      "time_s": result.reaction_time_s + result.signal_spacing_time_s + block.length_m / (block.speed_limit_kmh / 3.6), "position_m": block.length_m},
            {"event": "clearing_point_reached", "time_s": result.min_headway_s - result.overlap_time_s, "position_m": block.length_m + block.clearing_point_m},
            {"event": "headway_complete",       "time_s": result.min_headway_s, "position_m": block.length_m + block.clearing_point_m + 50},
        ]

        return {
            "block_id": block.section_id,
            "block_length_m": block.length_m,
            "min_headway_s": result.min_headway_s,
            "min_headway_min": round(result.min_headway_min, 2),
            "stairway": events,
            "components": result.components,
        }
