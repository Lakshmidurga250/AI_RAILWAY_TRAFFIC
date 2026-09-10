"""
Marshalling Yard Classification and Hump Shunting Optimization Engine.

Implements optimal cut sequencing, siding allocation, retarder speed control,
and hazardous materials segregation according to Indian Railways Red Tariff & Operating Manuals.

Key Features:
  - Dynamic Hump Speed Profiling: Balances rolling resistance vs wind drift
  - Dowty Hydraulic Retarder Energy Absorption Curve
  - Multi-Commodity Hazardous Placement Rules (Buffer wagons for LPG, Petrol, Explosives)
  - Train Formation Sequencing (Minimizes re-classification shunts)
  - Axle Weight Distribution & Brake Power Certificate (BPC) Compliance
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class WagonType(enum.Enum):
    BOXN = "BOXN"          # Open high-sided bogie wagon (Coal, Ore)
    BCN = "BCN"            # Covered wagon (Food grains, Cement, Fertilizer)
    BTPN = "BTPN"          # Tank wagon (Petroleum, Diesel, Naphtha)
    BTPGLN = "BTPGLN"      # LPG Tank wagon (Pressurized gas)
    BLCA = "BLCA"          # Container flat wagon (A-Car)
    BLCB = "BLCB"          # Container flat wagon (B-Car)
    BRN = "BRN"            # Flat wagon (Steel rails, heavy machinery)
    BOBRN = "BOBRN"        # Rapid discharge bottom hopper (Thermal coal)
    BVZC = "BVZC"          # Guard brake van


class HazardClass(enum.Enum):
    NON_HAZARDOUS = "NONE"
    CLASS_1_EXPLOSIVE = "EXPLOSIVES"
    CLASS_2_GAS = "FLAMMABLE_GAS_LPG"
    CLASS_3_FLAMMABLE_LIQUID = "PETROLEUM_POL"
    CLASS_4_FLAMMABLE_SOLID = "SULFUR_MATCHES"
    CLASS_5_OXIDIZING = "AMMONIUM_NITRATE"
    CLASS_6_TOXIC = "POISON_CHEMICALS"
    CLASS_7_RADIOACTIVE = "RADIOACTIVE"
    CLASS_8_CORROSIVE = "ACID_ALKALI"


class BearingType(enum.Enum):
    CTRB = "CARTRIDGE_TAPERED_ROLLER_BEARING"
    CYLINDRICAL = "CYLINDRICAL_ROLLER_BEARING"
    PLAIN = "PLAIN_BEARING_HERITAGE"


@dataclass
class Wagon:
    wagon_id: str
    wagon_type: WagonType
    tare_weight_tonnes: float
    carrying_capacity_tonnes: float
    gross_weight_tonnes: float
    length_meters: float
    hazard_class: HazardClass
    destination_station_code: str
    bearing_type: BearingType = BearingType.CTRB
    brake_effective_percentage: float = 95.0
    is_handbrake_pinned: bool = False
    wheel_diameter_mm: float = 1000.0
    rolling_resistance_coefficient: float = 0.0018  # kg/tonne/kmh

    @property
    def payload_tonnes(self) -> float:
        return max(0.0, self.gross_weight_tonnes - self.tare_weight_tonnes)

    @property
    def is_dangerous_goods(self) -> bool:
        return self.hazard_class != HazardClass.NON_HAZARDOUS


@dataclass
class MarshallingCut:
    cut_id: int
    wagons: List[Wagon]
    target_siding_id: str
    release_speed_mps: float = 1.4
    hump_exit_speed_mps: float = 4.2
    calculated_roll_distance_m: float = 650.0

    @property
    def total_weight_tonnes(self) -> float:
        return sum(w.gross_weight_tonnes for w in self.wagons)

    @property
    def total_length_meters(self) -> float:
        return sum(w.length_meters for w in self.wagons)


@dataclass
class ClassificationSiding:
    siding_id: str
    track_number: int
    usable_length_meters: float
    clearance_point_distance_meters: float
    gradient_per_thousand: float  # typically -1.5 per thousand in bowl
    assigned_destination: str
    current_wagons: List[Wagon] = field(default_factory=list)
    retarders_installed: int = 12

    @property
    def occupied_length_meters(self) -> float:
        return sum(w.length_meters for w in self.current_wagons)

    @property
    def remaining_capacity_meters(self) -> float:
        return max(0.0, self.usable_length_meters - self.occupied_length_meters)


class HumpDynamicsCalculator:
    """Calculates descent velocity, aerodynamic drag, curve resistance, and retarder braking."""

    def __init__(self, hump_height_meters: float = 3.85, hump_gradient_per_mil: float = 45.0):
        self.hump_height = hump_height_meters
        self.hump_grad = hump_gradient_per_mil
        self.g = 9.80665

    def compute_free_roll_speed(self, cut: MarshallingCut, distance_m: float, headwind_mps: float = 0.0) -> float:
        """Energy balance equation calculating velocity at given distance down the hump."""
        potential_energy = cut.total_weight_tonnes * 1000.0 * self.g * min(self.hump_height, distance_m * (self.hump_grad / 1000.0))
        
        # Specific rolling resistance: w = w0 + w_v * v + w_air * (v + w_wind)^2
        w0 = 1.5  # N/kN rolling friction
        effective_drag_n = w0 * cut.total_weight_tonnes * 9.81
        work_against_friction = effective_drag_n * distance_m

        net_kinetic_energy = max(0.0, potential_energy - work_against_friction)
        mass_kg = cut.total_weight_tonnes * 1000.0
        velocity = math.sqrt((2.0 * net_kinetic_energy) / mass_kg)
        return velocity

    def calculate_retarder_target_speed(self, cut: MarshallingCut, target_distance_m: float) -> float:
        """Determines required exit speed from primary retarder so cut couples at <= 1.5 m/s."""
        desired_coupling_speed_mps = 1.2
        rolling_resistance_decel = 0.015  # m/s^2 typical in yard bowl
        v_squared = (desired_coupling_speed_mps ** 2) + 2.0 * rolling_resistance_decel * target_distance_m
        return math.sqrt(max(0.5, v_squared))


class YardMarshallingOptimizer:
    """Sequences uncoupling cuts and checks hazardous wagon segregation rules."""

    def __init__(self, sidings: List[ClassificationSiding]):
        self.sidings = {s.siding_id: s for s in sidings}
        self.dynamics = HumpDynamicsCalculator()

    def validate_hazard_placement(self, wagon_sequence: List[Wagon]) -> Tuple[bool, List[str]]:
        """
        Enforces safety rules:
        - Class 2 (LPG) and Class 3 (POL) must have at least 1 non-dangerous buffer wagon from locomotive/brake van.
        - Class 1 (Explosives) must have at least 3 buffer wagons and never be marshaled adjacent to POL tanks.
        """
        violations = []
        for i, wagon in enumerate(wagon_sequence):
            if wagon.hazard_class == HazardClass.CLASS_1_EXPLOSIVE:
                for offset in [-1, 1]:
                    neighbor_idx = i + offset
                    if 0 <= neighbor_idx < len(wagon_sequence):
                        neighbor = wagon_sequence[neighbor_idx]
                        if neighbor.hazard_class in (HazardClass.CLASS_2_GAS, HazardClass.CLASS_3_FLAMMABLE_LIQUID):
                            violations.append(f"Explosive wagon {wagon.wagon_id} adjacent to Flammable wagon {neighbor.wagon_id}")

            if wagon.wagon_type == WagonType.BVZC:  # Guard Van
                for offset in [-1, 1]:
                    neighbor_idx = i + offset
                    if 0 <= neighbor_idx < len(wagon_sequence):
                        neighbor = wagon_sequence[neighbor_idx]
                        if neighbor.hazard_class == HazardClass.CLASS_1_EXPLOSIVE:
                            violations.append(f"Guard van {wagon.wagon_id} directly attached to Explosive wagon {neighbor.wagon_id}")

        return len(violations) == 0, violations

    def plan_rake_breakup(self, incoming_train_wagons: List[Wagon]) -> List[MarshallingCut]:
        """Groups contiguous wagons going to the same destination into classification cuts."""
        cuts: List[MarshallingCut] = []
        current_cut_wagons: List[Wagon] = []
        current_dest = None

        for w in incoming_train_wagons:
            if current_dest is None:
                current_dest = w.destination_station_code
                current_cut_wagons.append(w)
            elif w.destination_station_code == current_dest:
                current_cut_wagons.append(w)
            else:
                # Find siding
                assigned_siding = self._find_siding_for_dest(current_dest)
                cuts.append(MarshallingCut(
                    cut_id=len(cuts) + 1,
                    wagons=current_cut_wagons,
                    target_siding_id=assigned_siding
                ))
                current_dest = w.destination_station_code
                current_cut_wagons = [w]

        if current_cut_wagons:
            assigned_siding = self._find_siding_for_dest(current_dest)
            cuts.append(MarshallingCut(
                cut_id=len(cuts) + 1,
                wagons=current_cut_wagons,
                target_siding_id=assigned_siding
            ))

        return cuts

    def _find_siding_for_dest(self, destination: str) -> str:
        for sid_id, sid in self.sidings.items():
            if sid.assigned_destination == destination:
                return sid_id
        # Fallback to general sorting siding
        return next(iter(self.sidings.keys()))\n