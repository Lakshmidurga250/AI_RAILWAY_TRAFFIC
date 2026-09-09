"""Simulation & Scenario API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from backend.services.simulation_service import SimulationService
from backend.schemas.simulation import SimulationControl, SimulationStatusResponse, ScenarioComparisonResponse
from simulation.engine.digital_twin import digital_twin

router = APIRouter(prefix="/simulation", tags=["Simulation"])

@router.get("/status", response_model=SimulationStatusResponse)
def get_status():
    return SimulationService.get_status()

@router.get("/snapshot")
def get_digital_twin_snapshot():
    return digital_twin.get_live_snapshot()

@router.post("/control", response_model=SimulationStatusResponse)
def control_simulation(cmd: SimulationControl):
    act = cmd.action.lower()
    if act == "start":
        return SimulationService.start()
    elif act == "pause":
        return SimulationService.pause()
    elif act == "resume":
        return SimulationService.resume()
    elif act == "stop":
        return SimulationService.stop()
    elif act == "accelerate":
        return SimulationService.accelerate(cmd.acceleration_factor or 5.0)
    elif act == "step":
        return SimulationService.step(cmd.step_seconds or 1.0)
    elif act == "reset":
        return SimulationService.reset()
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action '{cmd.action}'")

@router.get("/scenarios")
def list_scenarios():
    return SimulationService.list_scenarios()

@router.post("/scenarios/{scenario_id}/compare", response_model=ScenarioComparisonResponse)
def compare_scenario(scenario_id: str):
    return SimulationService.run_scenario_comparison(scenario_id)
