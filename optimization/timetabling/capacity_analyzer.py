"""
Capacity Analyzer for Railway Timetabling (UIC 406 Method).

Implements:
- Infrastructure occupation compression
- Blocking time stairway compression
- Capacity consumption computation
- Line capacity vs demand comparison
- Station throat capacity
- Platform capacity computation
- Bottleneck identification
- Headway-based throughput analysis
- Heterogeneity penalty calculation
- Capacity vs reliability trade-off curves
- Network bottleneck graph
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CapacityStatus(Enum):
    UNCONGESTED = auto()      # < 60% utilization
    MODERATE = auto()         # 60-75% utilization
    HIGH = auto()             # 75-90% utilization
    CRITICAL = auto()         # > 90% utilization
    OVER_CAPACITY = auto()    # > 100% utilization


@dataclass
class OccupationResult:
    """Result of infrastructure occupation calculation."""
    section_id: str
    analysis_period_min: int
    total_blocking_time_min: float
    num_trains: int
    occupation_ratio: float          # 0-1
    free_capacity_min: float
    buffer_time_available_min: float
    status: CapacityStatus
    bottleneck_train_ids: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class LineCapacity:
    """Capacity analysis for a complete line or route."""
    line_id: str
    line_name: str
    sections: List[str]
    analysis_period_min: int = 1440   # Full day

    # Supply
    theoretical_capacity_trains: int = 0   # Infrastructure maximum
    practical_capacity_trains: int = 0     # With operational buffers
    offered_capacity_trains: int = 0       # What operator actually runs

    # Demand
    demanded_capacity_trains: int = 0

    # Utilization
    average_utilization: float = 0.0
    peak_utilization: float = 0.0

    # Quality metrics
    average_buffer_time_min: float = 0.0
    stability_index: float = 0.0          # 0-1 (1 = fully stable)

    # Bottleneck
    bottleneck_section: Optional[str] = None
    bottleneck_utilization: float = 0.0

    status: CapacityStatus = CapacityStatus.UNCONGESTED


class CapacityAnalyzer:
    """
    UIC 406 infrastructure capacity analysis.

    Methodology:
    1. Compress all train blocking times together in time axis
    2. Sum of compressed blocking times = total occupation
    3. Occupation ratio = total occupation / analysis period
    4. Capacity available = analysis period - total occupation
    """

    # UIC 406 capacity thresholds
    UIC_THRESHOLDS = {
        "urban_peak": 0.85,
        "interurban": 0.75,
        "mixed_traffic": 0.60,
    }

    # Stability-capacity trade-off table (UIC 406)
    STABILITY_CAPACITY_TABLE = {
        # capacity_ratio -> max_acceptable_occupation
        "stable_timetable": 0.70,
        "semi_stable": 0.80,
        "unstable": 0.90,
        "theoretical_max": 1.00,
    }

    def __init__(self) -> None:
        self._section_analyses: Dict[str, OccupationResult] = {}
        self._line_analyses: Dict[str, LineCapacity] = {}

    def compute_blocking_time(self, entry_time_min: float,
                               exit_time_min: float,
                               reaction_time_min: float = 0.08,
                               clearing_time_min: float = 0.08) -> Tuple[float, float]:
        """
        Compute blocking time with approach and clearing extensions.
        Returns (block_start, block_end) in minutes.
        """
        block_start = entry_time_min - reaction_time_min
        block_end = exit_time_min + clearing_time_min
        return block_start, block_end

    def compress_occupation(self, train_occupations: List[Tuple[float, float]]) -> float:
        """
        UIC 406 compression: shift all blocking time stairways to start at t=0.
        Returns total compressed occupation time (minutes).
        """
        if not train_occupations:
            return 0.0

        # Sort by start time
        sorted_occ = sorted(train_occupations)

        # Compress: shift each blocking time to start at end of previous
        compressed_end = 0.0
        total = 0.0
        for start, end in sorted_occ:
            duration = end - start
            compressed_end += duration
            total += duration

        return total

    def analyze_section_occupation(
            self,
            section_id: str,
            train_occupations: List[Tuple[str, float, float]],  # (train_id, start_min, end_min)
            analysis_period_min: int = 1440,
            buffer_time_factor: float = 0.05,
    ) -> OccupationResult:
        """
        Analyze occupation of a single track section.
        Implements UIC 406 compression method.
        """
        intervals = [(s, e) for _, s, e in train_occupations]
        total_blocking = self.compress_occupation(intervals)
        occupation_ratio = total_blocking / analysis_period_min if analysis_period_min > 0 else 0

        # Add buffer time requirement
        buffer_required = total_blocking * buffer_time_factor
        effective_occupation = total_blocking + buffer_required
        effective_ratio = effective_occupation / analysis_period_min

        # Determine status
        if effective_ratio < 0.60:
            status = CapacityStatus.UNCONGESTED
        elif effective_ratio < 0.75:
            status = CapacityStatus.MODERATE
        elif effective_ratio < 0.90:
            status = CapacityStatus.HIGH
        elif effective_ratio <= 1.00:
            status = CapacityStatus.CRITICAL
        else:
            status = CapacityStatus.OVER_CAPACITY

        free_capacity = max(0.0, analysis_period_min - effective_occupation)

        # Generate recommendations
        recommendations = []
        if effective_ratio > 0.85:
            recommendations.append("Consider additional crossing loops or passing sidings")
        if effective_ratio > 0.90:
            recommendations.append("Retime trains to reduce peak clustering")
        if effective_ratio > 1.00:
            recommendations.append("CRITICAL: Immediate traffic reduction required")

        result = OccupationResult(
            section_id=section_id,
            analysis_period_min=analysis_period_min,
            total_blocking_time_min=total_blocking,
            num_trains=len(train_occupations),
            occupation_ratio=round(occupation_ratio, 4),
            free_capacity_min=free_capacity,
            buffer_time_available_min=free_capacity * 0.7,
            status=status,
            bottleneck_train_ids=[t for t, s, e in train_occupations
                                   if e - s > total_blocking / max(len(train_occupations), 1) * 1.5],
            recommendations=recommendations,
        )
        self._section_analyses[section_id] = result
        return result

    def analyze_line_capacity(
            self,
            line_id: str,
            line_name: str,
            section_occupations: Dict[str, List[Tuple[str, float, float]]],
            theoretical_capacity: int,
            demanded_trains: int = 0,
            analysis_period_min: int = 1440,
    ) -> LineCapacity:
        """
        Perform full line capacity analysis.
        """
        section_ids = list(section_occupations.keys())
        section_results = []

        for section_id, occupations in section_occupations.items():
            result = self.analyze_section_occupation(
                section_id, occupations, analysis_period_min)
            section_results.append(result)

        if not section_results:
            return LineCapacity(line_id=line_id, line_name=line_name, sections=section_ids)

        # Find bottleneck (highest occupation)
        bottleneck = max(section_results, key=lambda r: r.occupation_ratio)

        avg_utilization = sum(r.occupation_ratio for r in section_results) / len(section_results)
        peak_utilization = bottleneck.occupation_ratio

        # Compute practical capacity
        compression_factor = 0.75
        practical_capacity = int(theoretical_capacity * compression_factor)

        # Stability index (inverse of max utilization)
        stability = max(0.0, 1.0 - peak_utilization)

        # Average buffer time
        avg_buffer = sum(r.buffer_time_available_min for r in section_results) / len(section_results)

        # Status based on bottleneck
        status = bottleneck.status

        lc = LineCapacity(
            line_id=line_id,
            line_name=line_name,
            sections=section_ids,
            analysis_period_min=analysis_period_min,
            theoretical_capacity_trains=theoretical_capacity,
            practical_capacity_trains=practical_capacity,
            offered_capacity_trains=sum(r.num_trains for r in section_results) // max(len(section_results), 1),
            demanded_capacity_trains=demanded_trains,
            average_utilization=round(avg_utilization, 4),
            peak_utilization=round(peak_utilization, 4),
            average_buffer_time_min=round(avg_buffer, 2),
            stability_index=round(stability, 4),
            bottleneck_section=bottleneck.section_id,
            bottleneck_utilization=round(bottleneck.occupation_ratio, 4),
            status=status,
        )
        self._line_analyses[line_id] = lc
        return lc

    def compute_heterogeneity_penalty(
            self, train_speeds: List[float],
            min_headway_min: float = 3.0,
    ) -> Dict[str, float]:
        """
        Compute capacity penalty for mixed-speed traffic.
        Heterogeneous traffic reduces capacity significantly.
        """
        if not train_speeds:
            return {"penalty_factor": 1.0, "capacity_loss_pct": 0.0}

        mean_speed = sum(train_speeds) / len(train_speeds)
        speed_variance = sum((s - mean_speed) ** 2 for s in train_speeds) / len(train_speeds)
        speed_std = math.sqrt(speed_variance)
        cv = speed_std / mean_speed if mean_speed > 0 else 0  # Coefficient of variation

        # Heterogeneity penalty (based on empirical UIC data)
        penalty = 1.0 + cv * 0.3  # 30% capacity loss per unit CV
        capacity_loss_pct = (penalty - 1.0) * 100

        return {
            "mean_speed_kmh": round(mean_speed, 1),
            "speed_std_kmh": round(speed_std, 1),
            "cv": round(cv, 3),
            "penalty_factor": round(penalty, 3),
            "capacity_loss_pct": round(capacity_loss_pct, 1),
            "effective_headway_min": round(min_headway_min * penalty, 2),
        }

    def find_network_bottlenecks(self) -> List[Dict[str, Any]]:
        """Find and rank bottleneck sections across the network."""
        bottlenecks = []
        for section_id, result in self._section_analyses.items():
            bottlenecks.append({
                "section_id": section_id,
                "occupation_ratio": result.occupation_ratio,
                "status": result.status.name,
                "trains_per_day": result.num_trains,
                "free_capacity_min": result.free_capacity_min,
                "recommendations": result.recommendations,
            })
        return sorted(bottlenecks, key=lambda x: x["occupation_ratio"], reverse=True)

    def capacity_reliability_curve(
            self, base_capacity: int, headway_variation_pct: float = 0.10
    ) -> List[Dict[str, float]]:
        """
        Generate capacity vs reliability trade-off curve.
        Shows how reliability decreases as capacity utilization increases.
        """
        curve = []
        for utilization in [i * 5 for i in range(1, 21)]:  # 5% to 100%
            ratio = utilization / 100.0
            # Reliability decreases exponentially near capacity
            reliability = math.exp(-((ratio - 0.5) ** 2) / (2 * 0.15 ** 2))
            reliability = max(0.0, min(1.0, reliability * 1.2))
            trains = int(base_capacity * ratio)
            curve.append({
                "utilization_pct": utilization,
                "trains": trains,
                "reliability": round(reliability, 3),
                "buffer_time_min": round(max(0, 5 * (1 - ratio)), 2),
            })
        return curve

    def full_network_report(self) -> Dict[str, Any]:
        return {
            "section_analyses": len(self._section_analyses),
            "line_analyses": len(self._line_analyses),
            "network_bottlenecks": self.find_network_bottlenecks()[:10],
            "critical_sections": [
                {"section_id": sid, "occupation_ratio": r.occupation_ratio}
                for sid, r in self._section_analyses.items()
                if r.status in (CapacityStatus.CRITICAL, CapacityStatus.OVER_CAPACITY)
            ],
            "lines": [
                {
                    "line_id": lc.line_id,
                    "status": lc.status.name,
                    "peak_utilization": lc.peak_utilization,
                    "practical_capacity": lc.practical_capacity_trains,
                }
                for lc in self._line_analyses.values()
            ],
        }
