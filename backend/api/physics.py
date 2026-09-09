"""Multi-Physics & Rolling Stock Dynamics API Endpoints."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from simulation.physics.wheel_rail_adhesion import WheelRailAdhesionModel, TrackAdhesionCondition
from simulation.physics.brake_pneumatics import BrakePneumaticModel, CouplerForceAnalyzer
from simulation.physics.catenary_power_flow import CatenarySubstationNetwork
from simulation.physics.rolling_stock_consist import RollingStockConsist

router = APIRouter(prefix="/physics", tags=["Multi-Physics"])


class AdhesionSimulationRequest(BaseModel):
    demanded_force_kn: float = 220.0
    adhesive_mass_tons: float = 160.0
    speed_kmh: float = 80.0
    rail_condition: TrackAdhesionCondition = TrackAdhesionCondition.WET_RAIN
    wsp_enabled: bool = True


class BrakeSimulationRequest(BaseModel):
    consist_length_m: float = 400.0
    wagon_count: int = 16
    target_pipe_pressure_bar: float = 0.0  # 0 = Emergency, 3.5 = Full Service
    elapsed_time_seconds: float = 2.5
    brake_mode: str = "PASSENGER"


class CatenarySimulationRequest(BaseModel):
    train_demands: List[Dict[str, Any]] = [
        {"train_id": "EXP_101", "location_km": 12.0, "mechanical_power_kw": 3200.0, "auxiliary_power_kw": 45.0},
        {"train_id": "REG_202", "location_km": 28.5, "mechanical_power_kw": -1800.0, "auxiliary_power_kw": 35.0},
        {"train_id": "FRT_303", "location_km": 54.0, "mechanical_power_kw": 4000.0, "auxiliary_power_kw": 20.0}
    ]


@router.get("/consists")
def list_available_consists():
    """Retrieve pre-configured industrial rolling stock consists."""
    hst = RollingStockConsist.create_high_speed_consist()
    emu = RollingStockConsist.create_intercity_emu_consist()
    freight = RollingStockConsist.create_heavy_freight_consist()
    return {
        "consists": [hst.to_dict(), emu.to_dict(), freight.to_dict()]
    }


@router.post("/simulate-adhesion")
def simulate_wheel_rail_adhesion(req: AdhesionSimulationRequest):
    """Simulate Polach wheel-rail contact mechanics, adhesion envelope, and WSP intervention."""
    demanded_n = req.demanded_force_kn * 1000.0
    return WheelRailAdhesionModel.evaluate_traction_limit(
        demanded_tractive_force_n=demanded_n,
        adhesive_mass_tons=req.adhesive_mass_tons,
        speed_kmh=req.speed_kmh,
        condition=req.rail_condition,
        wsp_enabled=req.wsp_enabled
    )


@router.post("/simulate-braking")
def simulate_pneumatic_braking(req: BrakeSimulationRequest):
    """Simulate UIC brake pipe acoustic wave propagation and in-train coupler buff/draft forces."""
    res = BrakePneumaticModel.simulate_brake_application(
        consist_length_m=req.consist_length_m,
        wagon_count=req.wagon_count,
        target_pipe_pressure_bar=req.target_pipe_pressure_bar,
        elapsed_time_s=req.elapsed_time_seconds,
        brake_mode=req.brake_mode
    )

    # Calculate resulting coupler forces
    mass_per_wagon = 55.0  # tons
    masses = [mass_per_wagon] * req.wagon_count
    efforts = [w["braking_effort_percentage"] for w in res["wagons"]]
    coupler_analysis = CouplerForceAnalyzer.compute_in_train_forces(masses, efforts)

    res["coupler_analysis"] = coupler_analysis
    return res


@router.post("/simulate-catenary")
def simulate_catenary_power_flow(req: CatenarySimulationRequest):
    """Solve 25kV AC catenary power flow, pantograph voltage drops, and regenerative receptivity."""
    network = CatenarySubstationNetwork()
    return network.solve_power_flow(req.train_demands)
