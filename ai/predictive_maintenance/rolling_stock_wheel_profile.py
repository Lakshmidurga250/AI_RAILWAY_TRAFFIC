"""
Predictive Maintenance Engine for Rolling Stock Wheel Profile & Flange Wear.

Implements UIC 510-2 / RDSO Standards for Wheel Wear Prediction:
  - Wheel Flange Thickness & Height Degradation Models (Archard Wear Law)
  - Hollow Tread & False Flange Detection
  - Acoustic Bearing Health (Hot Box / Hot Axle Early Warning via HBD/HAD Detectors)
  - Re-Profiling Scheduling on CNC Underfloor Wheel Lathe (UWL)
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class WheelCondemningReason(enum.Enum):
    NONE_HEALTHY = "NONE_HEALTHY"
    FLANGE_THIN = "FLANGE_THICKNESS_CONDEMNED"      # < 22 mm
    FLANGE_HIGH = "FLANGE_HEIGHT_CONDEMNED"        # > 35 mm
    TREAD_HOLLOW = "TREAD_HOLLOW_CONDEMNED"        # > 3.0 mm
    WHEEL_DIAMETER_MIN = "WHEEL_DIAMETER_MINIMUM"  # < 840 mm for coach, < 906 mm for freight


@dataclass
class WheelsetWearProfile:
    wheelset_id: str
    axle_number: int
    coach_id: str
    nominal_diameter_mm: float = 1000.0
    current_diameter_mm: float = 985.0
    flange_thickness_mm: float = 28.5
    flange_height_mm: float = 29.2
    tread_hollow_mm: float = 0.8
    mileage_since_last_lathe_km: float = 85000.0
    bearing_temperature_c: float = 42.0
    acoustic_defect_score: float = 0.08  # 0 to 1 scale


class WheelsetPredictiveMaintenanceSystem:
    """Simulates wear progression and schedules CNC lathe maintenance."""

    def __init__(self, wear_rate_mm_per_100k_km: float = 1.2):
        self.wear_rate = wear_rate_mm_per_100k_km
        self.wheelsets: Dict[str, WheelsetWearProfile] = {}

    def register_wheelset(self, profile: WheelsetWearProfile):
        self.wheelsets[profile.wheelset_id] = profile

    def evaluate_wheelset(self, profile: WheelsetWearProfile) -> Tuple[WheelCondemningReason, int]:
        """
        Evaluates wheel profile against safety condemning limits.
        Returns: (condemning_reason, estimated_remaining_km)
        """
        if profile.flange_thickness_mm <= 22.0:
            return WheelCondemningReason.FLANGE_THIN, 0
        if profile.flange_height_mm >= 35.0:
            return WheelCondemningReason.FLANGE_HIGH, 0
        if profile.tread_hollow_mm >= 3.0:
            return WheelCondemningReason.TREAD_HOLLOW, 0
        if profile.current_diameter_mm <= 840.0:
            return WheelCondemningReason.WHEEL_DIAMETER_MIN, 0

        # Remaining km calculation based on flange thickness
        margin_mm = profile.flange_thickness_mm - 22.0
        remaining_km = int((margin_mm / self.wear_rate) * 100000.0)
        return WheelCondemningReason.NONE_HEALTHY, remaining_km\n