"""Simulation schemas."""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SimulationControl(BaseModel):
    action: str  # start, stop, pause, resume, accelerate, step, reset
    acceleration_factor: Optional[float] = 1.0
    scenario_id: Optional[str] = None
    step_seconds: Optional[float] = 1.0

class SimulationStatusResponse(BaseModel):
    id: str
    name: str
    status: str
    mode: str
    time_acceleration: float
    current_sim_time: datetime
    start_time: datetime
    total_trains: int
    active_conflicts: int
    resolved_conflicts: int
    average_delay_minutes: float
    punctuality_percentage: float
    total_energy_kwh: float

    model_config = ConfigDict(from_attributes=True)

class ScenarioCreate(BaseModel):
    name: str
    scenario_type: str  # TRACK_CLOSURE, TRAIN_DELAY, SIGNAL_FAILURE, PASSENGER_SURGE, WEATHER, SPEED_RESTRICTION
    description: Optional[str] = "Custom dispatcher disruption scenario"
    parameters: Dict[str, Any] = {}

class ScenarioComparisonResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: Optional[str] = None
    baseline: Dict[str, Any]
    heuristic: Optional[Dict[str, Any]] = None
    optimized: Dict[str, Any]
    delay_reduction_percentage: Optional[float] = 0.0
    conflicts_avoided_percentage: Optional[float] = 0.0
    energy_savings_percentage: Optional[float] = 0.0
    improvement_metrics: Optional[Dict[str, Any]] = None
