"""
Dedicated Freight Corridor (DFC) Multi-Zonal Heavy Haul Simulator.

Simulates heavy haul train movements across Eastern and Western Dedicated Freight Corridors (EDFC / WDFC):
  - Double-Stack Container Trains (2x high-cube ISO containers on BLCA/BLCB wagons)
  - Long-Haul Combination Operations (Python / Super Anaconda: 3-4 rakes combined with LOCOTROL wireless DPU)
  - 25-Tonne & 32.5-Tonne Axle Load Track Dynamics & OHE 2x25 kV Traction Feeders
  - Automatic In-Motion Weighbridge (IMWB) Overload Detection
  - Feeder Route Junction Handovers between Indian Railways (IR) & DFCCIL Networks
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class CorridorZone(enum.Enum):
    WDFC_DADRI_JNPT = "WDFC_DADRI_TO_JNPT"
    EDFC_LUDHIANA_SONNAGAR = "EDFC_LUDHIANA_TO_SONNAGAR"
    EAST_COAST_DEDICATED = "EAST_COAST_KHARAGPUR_VIJAYAWADA"
    NORTH_SOUTH_SUB_CORRIDOR = "NORTH_SOUTH_ITANSI_VIJAYAWADA"


class FreightTrainFormation(enum.Enum):
    SINGLE_RAKE_BOXN = "SINGLE_RAKE_BOXN_58_WAGONS"
    DOUBLE_STACK_CONTAINER = "DOUBLE_STACK_CONTAINER_45_WAGONS"
    PYTHON_DOUBLE_RAKE = "PYTHON_2_RAKES_COMBINED_116_WAGONS"
    SUPER_ANACONDA_TRIPLE_RAKE = "SUPER_ANACONDA_3_RAKES_177_WAGONS"
    RORO_TRUCK_ON_TRAIN = "ROLL_ON_ROLL_OFF_TRUCK_TRAIN"


@dataclass
class TractionLocomotive:
    loco_number: str
    loco_class: str = "WAG-12B"  # 12,000 HP Twin Bo-Bo Electric Locomotive
    rated_power_kw: float = 9000.0
    max_starting_tractive_effort_kn: float = 706.0
    continuous_tractive_effort_kn: float = 540.0
    locotrol_master_mode: bool = True  # True if Lead Master, False if Remote Distributed Power Unit (DPU)


@dataclass
class HeavyHaulTrain:
    train_number: str
    formation_type: FreightTrainFormation
    lead_locomotive: TractionLocomotive
    trailing_dpu_locomotives: List[TractionLocomotive]
    total_wagons: int
    gross_trailing_load_tonnes: float
    train_length_meters: float
    current_speed_kmh: float = 0.0
    current_km: float = 0.0
    target_destination_yard: str = "JNPT_PORT_YARD"
    is_dpu_wireless_link_synced: bool = True


class DFCCorridorSimulator:
    """Manages heavy haul corridor dispatching, energy recovery, and LOCOTROL synchronization."""

    def __init__(self, zone: CorridorZone, max_permissible_speed_kmh: float = 100.0):
        self.zone = zone
        self.mps = max_permissible_speed_kmh
        self.active_trains: Dict[str, HeavyHaulTrain] = {}

    def register_train(self, train: HeavyHaulTrain):
        self.active_trains[train.train_number] = train

    def compute_tractive_balance(self, train: HeavyHaulTrain, gradient_per_mil: float) -> Tuple[float, float]:
        """
        Computes total available tractive effort vs total resistance:
        R_total = R_rolling + R_gradient + R_curve + R_aerodynamic
        """
        all_locos = [train.lead_locomotive] + train.trailing_dpu_locomotives
        total_te_kn = sum(l.continuous_tractive_effort_kn for l in all_locos)

        # Davis formula for heavy haul: R = (1.3 + 29/w + b*v + c*A*v^2 / W) * W
        mass_tonnes = train.gross_trailing_load_tonnes
        v_mps = train.current_speed_kmh / 3.6
        rolling_res_kn = (0.0015 * mass_tonnes * 9.81)
        gradient_res_kn = (gradient_per_mil / 1000.0) * mass_tonnes * 9.81
        aero_res_kn = 0.00045 * (v_mps ** 2) * 12.0  # Double stack frontal area ~ 12m2

        total_res_kn = rolling_res_kn + gradient_res_kn + aero_res_kn
        net_accel_mps2 = max(-1.2, (total_te_kn - total_res_kn) / (mass_tonnes * 1.10))

        return total_te_kn, net_accel_mps2

    def verify_locotrol_dpu_safety(self, train: HeavyHaulTrain) -> Tuple[bool, str]:
        """Ensures brake pipe synchronization between lead and rear slave locomotives."""
        if train.formation_type in (FreightTrainFormation.PYTHON_DOUBLE_RAKE, FreightTrainFormation.SUPER_ANACONDA_TRIPLE_RAKE):
            if not train.is_dpu_wireless_link_synced:
                return False, "CRITICAL: LOCOTROL radio link desynchronized. Emergency penalty brake applied."
            if len(train.trailing_dpu_locomotives) < 1:
                return False, "Configuration error: Long haul train requires distributed power unit."
        return True, "LOCOTROL DPU Telemetry Healthy."\n