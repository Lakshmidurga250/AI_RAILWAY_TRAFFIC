"""Rolling Stock Consist Configuration and Vehicle Composition Engine.

Enables detailed vehicle-by-vehicle train formation with accurate axle load distributions,
total gross mass, powered adhesive weight fractions, and aerodynamic resistance scaling.
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ConsistType(str, Enum):
    HIGH_SPEED_HST = "HIGH_SPEED_HST"
    INTERCITY_EMU = "INTERCITY_EMU"
    REGIONAL_COMMUTER = "REGIONAL_COMMUTER"
    HEAVY_HAUL_FREIGHT = "HEAVY_HAUL_FREIGHT"
    CONTAINER_INTERMODAL = "CONTAINER_INTERMODAL"


class VehicleUnit(BaseModel):
    unit_id: str
    unit_type: str  # LOCOMOTIVE, PASSENGER_COACH, FREIGHT_WAGON, CAB_CAR
    length_m: float
    tare_mass_tons: float
    payload_mass_tons: float = 0.0
    axle_count: int = 4
    is_powered: bool = False
    traction_power_kw: float = 0.0
    max_tractive_effort_kn: float = 0.0

    @property
    def gross_mass_tons(self) -> float:
        return self.tare_mass_tons + self.payload_mass_tons

    @property
    def axle_load_tons(self) -> float:
        return self.gross_mass_tons / max(1, self.axle_count)


class RollingStockConsist:
    """Represents a configured multi-vehicle railway train consist."""

    def __init__(
        self,
        consist_id: str,
        name: str,
        consist_type: ConsistType,
        vehicles: List[VehicleUnit],
        max_operating_speed_kmh: float = 160.0
    ):
        self.consist_id = consist_id
        self.name = name
        self.consist_type = consist_type
        self.vehicles = vehicles
        self.max_operating_speed_kmh = max_operating_speed_kmh

    @property
    def total_length_m(self) -> float:
        return sum(v.length_m for v in self.vehicles)

    @property
    def total_mass_tons(self) -> float:
        return sum(v.gross_mass_tons for v in self.vehicles)

    @property
    def adhesive_mass_tons(self) -> float:
        return sum(v.gross_mass_tons for v in self.vehicles if v.is_powered)

    @property
    def total_axles(self) -> int:
        return sum(v.axle_count for v in self.vehicles)

    @property
    def total_power_kw(self) -> float:
        return sum(v.traction_power_kw for v in self.vehicles if v.is_powered)

    @property
    def max_tractive_effort_kn(self) -> float:
        return sum(v.max_tractive_effort_kn for v in self.vehicles if v.is_powered)

    @property
    def davis_coefficients(self) -> Dict[str, float]:
        """Calibrated Davis equation coefficients [A, B, C] for this specific consist."""
        n_wagons = len(self.vehicles)
        if self.consist_type == ConsistType.HIGH_SPEED_HST:
            # Streamlined nose and inter-car bogie skirts
            return {"A": 2.0, "B": 0.025, "C": 0.0012 + (n_wagons * 0.00008)}
        elif self.consist_type == ConsistType.HEAVY_HAUL_FREIGHT:
            # High mechanical resistance and bluff boxy wagon drag
            return {"A": 3.8, "B": 0.045, "C": 0.0035 + (n_wagons * 0.00015)}
        else:
            # Standard passenger EMU
            return {"A": 2.5, "B": 0.035, "C": 0.0018 + (n_wagons * 0.00010)}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consist_id": self.consist_id,
            "name": self.name,
            "consist_type": self.consist_type.value,
            "vehicle_count": len(self.vehicles),
            "total_length_m": round(self.total_length_m, 1),
            "total_mass_tons": round(self.total_mass_tons, 1),
            "adhesive_mass_tons": round(self.adhesive_mass_tons, 1),
            "total_axles": self.total_axles,
            "total_power_kw": round(self.total_power_kw, 1),
            "max_tractive_effort_kn": round(self.max_tractive_effort_kn, 1),
            "max_operating_speed_kmh": self.max_operating_speed_kmh,
            "davis_coefficients": self.davis_coefficients
        }

    # Factory presets for industrial testing
    @classmethod
    def create_high_speed_consist(cls, consist_id: str = "HST_EXPRESS_8") -> "RollingStockConsist":
        """8-car High Speed Train (2 power cars + 6 articulated trailers)."""
        vehicles = [
            VehicleUnit(
                unit_id="LOC_HST_1", unit_type="LOCOMOTIVE", length_m=22.0,
                tare_mass_tons=78.0, is_powered=True, traction_power_kw=4800.0, max_tractive_effort_kn=280.0
            )
        ]
        for i in range(1, 7):
            vehicles.append(VehicleUnit(
                unit_id=f"CAR_HST_{i}", unit_type="PASSENGER_COACH", length_m=25.0,
                tare_mass_tons=42.0, payload_mass_tons=6.5, is_powered=False
            ))
        vehicles.append(VehicleUnit(
            unit_id="LOC_HST_2", unit_type="LOCOMOTIVE", length_m=22.0,
            tare_mass_tons=78.0, is_powered=True, traction_power_kw=4800.0, max_tractive_effort_kn=280.0
        ))
        return cls(consist_id, "Vande / Eurostar High-Speed Consist", ConsistType.HIGH_SPEED_HST, vehicles, 250.0)

    @classmethod
    def create_intercity_emu_consist(cls, consist_id: str = "EMU_INTERCITY_6") -> "RollingStockConsist":
        """6-car Distributed Traction Intercity EMU (3 motor coaches, 3 trailer coaches)."""
        vehicles = []
        for i in range(1, 7):
            is_motor = (i % 2 == 1)
            vehicles.append(VehicleUnit(
                unit_id=f"EMU_VEH_{i}",
                unit_type="CAB_CAR" if i in (1, 6) else "PASSENGER_COACH",
                length_m=24.0,
                tare_mass_tons=46.0,
                payload_mass_tons=8.0,
                is_powered=is_motor,
                traction_power_kw=1600.0 if is_motor else 0.0,
                max_tractive_effort_kn=120.0 if is_motor else 0.0
            ))
        return cls(consist_id, "Corridor Rapid Intercity EMU", ConsistType.INTERCITY_EMU, vehicles, 160.0)

    @classmethod
    def create_heavy_freight_consist(cls, consist_id: str = "FREIGHT_BULK_40") -> "RollingStockConsist":
        """Heavy haul mineral freight train (2 heavy locomotives + 38 bulk wagons = ~3,200 tons)."""
        vehicles = [
            VehicleUnit(
                unit_id="LOCO_HEAVY_1", unit_type="LOCOMOTIVE", length_m=21.0,
                tare_mass_tons=130.0, axle_count=6, is_powered=True, traction_power_kw=4500.0, max_tractive_effort_kn=450.0
            ),
            VehicleUnit(
                unit_id="LOCO_HEAVY_2", unit_type="LOCOMOTIVE", length_m=21.0,
                tare_mass_tons=130.0, axle_count=6, is_powered=True, traction_power_kw=4500.0, max_tractive_effort_kn=450.0
            )
        ]
        for i in range(1, 39):
            vehicles.append(VehicleUnit(
                unit_id=f"WAGON_HOPPER_{i}", unit_type="FREIGHT_WAGON", length_m=14.0,
                tare_mass_tons=22.0, payload_mass_tons=58.0, is_powered=False
            ))
        return cls(consist_id, "Heavy Haul Mineral Freight", ConsistType.HEAVY_HAUL_FREIGHT, vehicles, 100.0)
