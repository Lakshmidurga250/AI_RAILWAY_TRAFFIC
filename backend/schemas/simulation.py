"""Simulation schemas."""
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

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

    class Config:
        from_attributes = True

class ScenarioCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    scenario_type: str  # TRACK_CLOSURE, TRAIN_DELAY, SIGNAL_FAILURE, PASSENGER_SURGE, WEATHER
    parameters: Dict[str, Any]

class ScenarioComparisonResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    baseline: Dict[str, Any]
    optimized: Dict[str, Any]
    improvement_metrics: Dict[str, Any]
