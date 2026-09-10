"""
Traction Substation (TSS) & 2x25 kV Autotransformer SCADA Grid Simulator.

Models national high-voltage railway electrification distribution:
  - 132kV / 220kV Grid Infeed to 25kV Catenary / Contact Wire
  - 2x25 kV System with +25kV Catenary, -25kV Feeder, and 0V Rail Return
  - Harmonic Distortion & Power Factor Active Filtering (SVC / STATCOM)
  - Sectioning and Paralleling Posts (SP / SSP) Neutral Section Switching
  - Fault Detection: Distance relays (Mho / Quadrilateral) for Catenary-to-Earth faults
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class NeutralSectionState(enum.Enum):
    CONNECTED_UP_LINE = "CONNECTED_UP_LINE"
    CONNECTED_DOWN_LINE = "CONNECTED_DOWN_LINE"
    ISOLATED_DEAD_ZONE = "ISOLATED_DEAD_ZONE"
    PARALLELED = "PARALLELED"


@dataclass
class TractionSubstation:
    tss_id: str
    grid_supply_voltage_kv: float = 132.0
    transformer_mva_rating: float = 30.0
    catenary_voltage_kv: float = 27.5
    active_load_mw: float = 14.2
    reactive_load_mvar: float = 4.8
    statcom_compensation_mvar: float = 4.0
    temperature_celsius: float = 48.0
    circuit_breaker_closed: bool = True

    @property
    def apparent_power_mva(self) -> float:
        net_mvar = max(0.0, self.reactive_load_mvar - self.statcom_compensation_mvar)
        return math.sqrt(self.active_load_mw ** 2 + net_mvar ** 2)

    @property
    def power_factor(self) -> float:
        s = self.apparent_power_mva
        return 1.0 if s <= 0 else self.active_load_mw / s


class SCADAElectrificationGrid:
    """Monitors and manages national traction power feed network."""

    def __init__(self):
        self.substations: Dict[str, TractionSubstation] = {}

    def add_substation(self, tss: TractionSubstation):
        self.substations[tss.tss_id] = tss

    def calculate_voltage_drop(self, tss_id: str, distance_from_tss_km: float, current_amperes: float) -> float:
        """Computes voltage drop along catenary conductor: Delta_V = I * (R*cos_phi + X*sin_phi) * L."""
        r_per_km = 0.14  # Ohms/km copper contact wire + catenary
        x_per_km = 0.28  # Ohms/km inductance
        cos_phi = 0.92
        sin_phi = math.sqrt(1.0 - cos_phi ** 2)

        impedance_drop_volts = current_amperes * (r_per_km * cos_phi + x_per_km * sin_phi) * distance_from_tss_km
        return impedance_drop_volts / 1000.0  # in kV\n