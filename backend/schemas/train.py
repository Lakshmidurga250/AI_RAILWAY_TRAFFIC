"""Train schemas."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class ScheduleStopSchema(BaseModel):
    id: Optional[int] = None
    station_id: str
    platform_id: Optional[str] = None
    stop_sequence: int
    scheduled_arrival: Optional[datetime] = None
    scheduled_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    dwell_duration_seconds: int = 120
    status: str = "PENDING"

    model_config = ConfigDict(from_attributes=True)

class TrainCreate(BaseModel):
    id: str
    train_number: str
    name: str
    train_type: str = "INTERCITY"
    origin_station_id: str
    destination_station_id: str
    length_m: float = 200.0
    weight_tons: float = 450.0
    max_speed_kmh: float = 160.0
    acceleration_ms2: float = 0.8
    braking_ms2: float = 1.0
    passenger_capacity: int = 600
    priority: int = 5
    scheduled_departure: datetime
    scheduled_arrival: datetime

class TrainUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    current_speed_kmh: Optional[float] = None
    current_track_id: Optional[str] = None
    current_platform_id: Optional[str] = None
    current_delay_minutes: Optional[float] = None

class TrainResponse(BaseModel):
    id: str
    train_number: str
    name: str
    train_type: str
    origin_station_id: str
    destination_station_id: str
    length_m: float
    weight_tons: float
    max_speed_kmh: float
    acceleration_ms2: float
    braking_ms2: float
    passenger_capacity: int
    current_passengers: int
    priority: int
    status: str
    current_speed_kmh: float
    current_track_id: Optional[str] = None
    current_platform_id: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    progress_percentage: float
    scheduled_departure: datetime
    scheduled_arrival: datetime
    estimated_departure: Optional[datetime] = None
    estimated_arrival: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    current_delay_minutes: float
    cumulative_energy_kwh: float
    regenerated_energy_kwh: float
    schedules: List[ScheduleStopSchema] = []

    model_config = ConfigDict(from_attributes=True)

class TelemetryPoint(BaseModel):
    train_id: str
    timestamp: datetime
    speed_kmh: float
    latitude: float
    longitude: float
    current_track_id: Optional[str] = None
    power_draw_kw: float = 0.0
    current_delay_min: float = 0.0
    passenger_count: int = 0
