"""Analytics and KPI schemas."""
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class KPISummary(BaseModel):
    active_trains: int
    punctuality_rate: float
    average_delay_minutes: float
    max_delay_minutes: float
    total_conflicts_active: int
    total_conflicts_resolved_today: int
    network_throughput_tph: float  # trains per hour
    total_energy_kwh: float
    co2_saved_kg: float
    platform_occupancy_rate: float
    track_utilization_rate: float

class DelayDistribution(BaseModel):
    on_time: int
    minor_delay: int  # 1-5 min
    moderate_delay: int  # 5-15 min
    severe_delay: int  # >15 min
    cancelled: int

class StationUtilization(BaseModel):
    station_id: str
    station_name: str
    trains_handled: int
    occupancy_rate: float
    congestion_index: float

class AnalyticsDashboardData(BaseModel):
    kpis: KPISummary
    delay_distribution: DelayDistribution
    hourly_punctuality: List[Dict[str, Any]]
    station_utilization: List[StationUtilization]
    energy_trend: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]] = []
    timestamp: datetime
