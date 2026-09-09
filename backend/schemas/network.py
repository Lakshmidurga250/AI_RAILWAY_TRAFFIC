"""Network schemas: Stations, Platforms, Tracks, Signals, Junctions, Switches."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class PlatformSchema(BaseModel):
    id: str
    station_id: str
    platform_number: str
    length: float = 400.0
    capacity: int = 1
    is_occupied: bool = False
    current_train_id: Optional[str] = None
    status: str = "AVAILABLE"
    has_overhead_catenary: bool = True

    model_config = ConfigDict(from_attributes=True)

class StationSchema(BaseModel):
    id: str
    name: str
    code: str
    latitude: float
    longitude: float
    zone: str = "Central"
    passenger_capacity: int = 5000
    current_occupancy: int = 0
    status: str = "OPERATIONAL"
    platforms: List[PlatformSchema] = []

    model_config = ConfigDict(from_attributes=True)

class TrackSchema(BaseModel):
    id: str
    name: str
    source_node: str
    target_node: str
    length: float
    max_speed: float = 160.0
    gradient: float = 0.0
    electrified: bool = True
    track_type: str = "MAINLINE"
    is_bidirectional: bool = False
    status: str = "CLEAR"
    current_train_id: Optional[str] = None
    speed_restriction: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class JunctionSchema(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    max_throughput: int = 24
    current_load: int = 0
    status: str = "CLEAR"

    model_config = ConfigDict(from_attributes=True)

class SignalSchema(BaseModel):
    id: str
    track_id: str
    location_km: float = 0.0
    aspect: str = "GREEN"
    signal_type: str = "AUTOMATIC"
    is_faulty: bool = False

    model_config = ConfigDict(from_attributes=True)

class SwitchSchema(BaseModel):
    id: str
    junction_id: str
    state: str = "NORMAL"
    is_locked: bool = False
    locked_for_train_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class NetworkGraphResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]
    stations_count: int
    tracks_count: int
    junctions_count: int
