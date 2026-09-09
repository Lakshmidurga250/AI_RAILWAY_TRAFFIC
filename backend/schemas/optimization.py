"""Optimization schemas."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class RouteOptimizationRequest(BaseModel):
    train_id: str
    origin_station_id: str
    destination_station_id: str
    algorithm: str = "A_STAR"  # DIJKSTRA, A_STAR, GENETIC, MULTI_OBJECTIVE
    weights: Optional[Dict[str, float]] = None  # time, delay, congestion, energy, conflicts

class RouteOption(BaseModel):
    route_id: str
    track_ids: List[str]
    station_ids: List[str]
    total_distance_km: float
    estimated_travel_time_min: float
    estimated_energy_kwh: float
    congestion_score: float
    conflicts_count: int
    composite_score: float

class RouteOptimizationResponse(BaseModel):
    train_id: str
    algorithm: str
    optimal_route: RouteOption
    alternative_routes: List[RouteOption] = []
    execution_time_ms: float
    explanation: str

class PlatformOptimizationRequest(BaseModel):
    station_id: str
    train_id: str
    arrival_time: datetime
    departure_time: datetime

class PlatformOptimizationResponse(BaseModel):
    station_id: str
    train_id: str
    recommended_platform_id: str
    platform_number: str
    alternative_platforms: List[Dict[str, Any]]
    score: float
    conflicts_avoided: int
    accessibility_rating: float
    explanation: str

class ReschedulingRequest(BaseModel):
    scenario_type: str = "TRACK_CLOSURE"  # TRACK_CLOSURE, TRAIN_FAILURE, SIGNAL_FAILURE, SEVERE_DELAY
    affected_resource_id: str
    duration_minutes: int = 60

class ReschedulingResponse(BaseModel):
    scenario_type: str
    affected_resource_id: str
    affected_trains_count: int
    revised_schedule: List[Dict[str, Any]]
    rerouted_trains: List[Dict[str, Any]]
    baseline_delay_minutes: float
    optimized_delay_minutes: float
    delay_reduction_percentage: float
    explanation: str

class EnergyOptimizationRequest(BaseModel):
    train_id: str
    target_arrival_time: Optional[datetime] = None

class EnergyOptimizationResponse(BaseModel):
    train_id: str
    baseline_energy_kwh: float
    optimized_energy_kwh: float
    energy_savings_percentage: float
    co2_reduction_kg: float
    speed_profile: List[Dict[str, float]]
    explanation: str

class OptimizationRunResponse(BaseModel):
    id: str
    optimization_type: str
    algorithm: str
    status: str
    execution_time_ms: float
    baseline_delay_minutes: float
    optimized_delay_minutes: float
    delay_reduction_percentage: float
    baseline_energy_kwh: float
    optimized_energy_kwh: float
    energy_savings_percentage: float
    conflicts_resolved: int
    throughput_increase_percentage: float
    input_parameters: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    created_at: datetime

class RLTrainRequest(BaseModel):
    episodes: int = 10
    max_steps_per_episode: int = 25
    algorithm: str = "DQN"  # DQN, PPO
    use_action_masking: bool = True

class RLTrainResponse(BaseModel):
    run_id: str
    algorithm: str
    episodes_trained: int
    mean_episode_reward: float
    shield_interventions_count: int
    improvement_percentage: float
    execution_time_ms: float

class RLDispatchRequest(BaseModel):
    train_id: str
    algorithm: str = "DQN"  # DQN, PPO, RULE_BASED
    use_safety_shield: bool = True

class RLDispatchResponse(BaseModel):
    train_id: str
    algorithm: str
    proposed_action: str
    executed_action: str
    shield_intervened: bool
    violations: List[str] = []
    reason: str
    action_mask: List[bool] = []

class RLTrainingRunResponse(BaseModel):
    id: str
    algorithm: str
    episodes_trained: int
    mean_episode_reward: float
    shield_interventions_count: int
    baseline_heuristic_reward: float
    improvement_percentage: float
    created_at: datetime


