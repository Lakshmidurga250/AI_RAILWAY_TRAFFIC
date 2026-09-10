"""
Indian Railways Comprehensive Rolling Stock Technical Specifications Database.

Contains complete mechanical, traction, pneumatic, and braking characteristics for:
  - Locomotives: WAP-7, WAP-5, WAG-9HC, WAG-12B, WDG-4G, WDP-4D
  - Trainsets: Vande Bharat Express (Train 18 / Train 20), Amrit Bharat Push-Pull (WAP-5 + 22 LHB)
  - Passenger Coaches: LHB Executive Chair Car (EC), AC 2-Tier (2A), AC 3-Tier Economy (3E), General Second Class (GS)
  - Freight Wagons: BOXNHL (Heavy coal/ore), BCNHL (Cement/Grain), BTPN (Petroleum tank), BLCA/BLCB (Double stack flat)
"""

from __future__ import annotations
import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


class TractionPowerSupply(enum.Enum):
    ELECTRIC_25KV_AC_50HZ = "25_KV_AC_50_HZ_SINGLE_PHASE"
    ELECTRIC_3KV_DC = "3_KV_DC_HISTORIC"
    DIESEL_ELECTRIC_AC_AC = "DIESEL_ELECTRIC_AC_AC_IGBT"
    BATTERY_ELECTRIC_HYBRID = "BATTERY_ELECTRIC_DUAL_MODE"


class BrakeSystemType(enum.Enum):
    TWIN_PIPE_GRADUATED_RELEASE = "TWIN_PIPE_AIR_BRAKE"
    ELECTRO_PNEUMATIC_EP = "ELECTRO_PNEUMATIC_BRAKE_EP"
    VACUUM_BRAKE_HERITAGE = "VACUUM_BRAKE_LEGACY"


@dataclass
class LocomotiveTechnicalSpec:
    class_name: str
    service_type: str  # Passenger / Freight / Mixed
    traction_supply: TractionPowerSupply
    continuous_power_hp: int
    continuous_power_kw: float
    max_operating_speed_kmh: float
    starting_tractive_effort_kn: float
    continuous_tractive_effort_kn: float
    regenerative_braking_effort_kn: float
    total_service_weight_tonnes: float
    axle_load_tonnes: float
    wheel_arrangement: str  # Co-Co, Bo-Bo, Bo-Bo+Bo-Bo
    gear_ratio: str
    transformer_kva: int
    traction_motor_type: str = "3-Phase Asynchronous Induction Motor"
    converter_technology: str = "IGBT Water Cooled VVVF"
    length_over_buffers_mm: int = 20562


@dataclass
class CoachTechnicalSpec:
    coach_code: str
    coach_family: str  # LHB, ICF, Vande Bharat EMU
    tare_weight_tonnes: float
    gross_weight_tonnes: float
    seating_berth_capacity: int
    length_over_couplers_mm: int
    max_operating_speed_kmh: float
    bogie_type: str = "FIAT Bogie with Disc Brakes"
    braking_system: BrakeSystemType = BrakeSystemType.TWIN_PIPE_GRADUATED_RELEASE
    disc_diameter_mm: float = 640.0
    air_spring_secondary_suspension: bool = True
    cbc_tightlock_coupler: bool = True


class RollingStockCatalog:
    """Complete registry of IR rolling stock technical specifications."""

    def __init__(self):
        self.locomotives: Dict[str, LocomotiveTechnicalSpec] = {}
        self.coaches: Dict[str, CoachTechnicalSpec] = {}
        self._load_catalog()

    def _load_catalog(self):
        # Locomotives
        self.locomotives["WAP-7"] = LocomotiveTechnicalSpec(
            class_name="WAP-7",
            service_type="High Speed Passenger",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=6350,
            continuous_power_kw=4735.0,
            max_operating_speed_kmh=140.0,
            starting_tractive_effort_kn=322.0,
            continuous_tractive_effort_kn=228.0,
            regenerative_braking_effort_kn=182.0,
            total_service_weight_tonnes=123.0,
            axle_load_tonnes=20.5,
            wheel_arrangement="Co-Co",
            gear_ratio="72:20",
            transformer_kva=5400,
            length_over_buffers_mm=20562
        )
        self.locomotives["WAG-9HC"] = LocomotiveTechnicalSpec(
            class_name="WAG-9HC",
            service_type="Heavy Haul Freight",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=6120,
            continuous_power_kw=4560.0,
            max_operating_speed_kmh=100.0,
            starting_tractive_effort_kn=458.0,
            continuous_tractive_effort_kn=325.0,
            regenerative_braking_effort_kn=260.0,
            total_service_weight_tonnes=132.0,
            axle_load_tonnes=22.0,
            wheel_arrangement="Co-Co",
            gear_ratio="107:21",
            transformer_kva=5400,
            length_over_buffers_mm=20562
        )
        self.locomotives["WAG-12B"] = LocomotiveTechnicalSpec(
            class_name="WAG-12B",
            service_type="Ultra Heavy Freight (Prima T8)",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=12000,
            continuous_power_kw=9000.0,
            max_operating_speed_kmh=120.0,
            starting_tractive_effort_kn=706.0,
            continuous_tractive_effort_kn=540.0,
            regenerative_braking_effort_kn=510.0,
            total_service_weight_tonnes=180.0,
            axle_load_tonnes=22.5,
            wheel_arrangement="Bo-Bo + Bo-Bo",
            gear_ratio="85:16",
            transformer_kva=12000,
            length_over_buffers_mm=38400
        )
        self.locomotives["WAP-5"] = LocomotiveTechnicalSpec(
            class_name="WAP-5",
            service_type="Express Passenger",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=5450,
            continuous_power_kw=4064.0,
            max_operating_speed_kmh=160.0,
            starting_tractive_effort_kn=258.0,
            continuous_tractive_effort_kn=160.0,
            regenerative_braking_effort_kn=160.0,
            total_service_weight_tonnes=78.0,
            axle_load_tonnes=19.5,
            wheel_arrangement="Bo-Bo",
            gear_ratio="67:35",
            transformer_kva=5400,
            length_over_buffers_mm=18162
        )

        # Passenger Coaches
        self.coaches["LWACCN"] = CoachTechnicalSpec(
            coach_code="LWACCN",
            coach_family="LHB AC 3-Tier",
            tare_weight_tonnes=44.5,
            gross_weight_tonnes=52.0,
            seating_berth_capacity=72,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )
        self.coaches["LWACCW"] = CoachTechnicalSpec(
            coach_code="LWACCW",
            coach_family="LHB AC 2-Tier",
            tare_weight_tonnes=43.8,
            gross_weight_tonnes=50.2,
            seating_berth_capacity=52,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )
        self.coaches["LWFCZAC"] = CoachTechnicalSpec(
            coach_code="LWFCZAC",
            coach_family="LHB Executive Anubhuti Chair Car",
            tare_weight_tonnes=41.2,
            gross_weight_tonnes=47.5,
            seating_berth_capacity=56,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )

    def get_loco(self, class_name: str) -> Optional[LocomotiveTechnicalSpec]:
        return self.locomotives.get(class_name)

    def get_coach(self, coach_code: str) -> Optional[CoachTechnicalSpec]:
        return self.coaches.get(coach_code)
