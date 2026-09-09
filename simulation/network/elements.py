"""Railway Network Structural Elements."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SignalAspect(str, Enum):
    GREEN = "GREEN"           # Clear: Proceed at track speed
    DOUBLE_YELLOW = "DOUBLE_YELLOW" # Preliminary Caution: Next signal is yellow
    YELLOW = "YELLOW"         # Caution: Expect next signal at red
    RED = "RED"               # Danger: Stop immediately

class TrackStatus(str, Enum):
    CLEAR = "CLEAR"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED = "BLOCKED"
    SPEED_RESTRICTED = "SPEED_RESTRICTED"

class SwitchState(str, Enum):
    NORMAL = "NORMAL"   # Mainline alignment
    REVERSE = "REVERSE" # Diverging route alignment

class PlatformElement(BaseModel):
    id: str
    station_id: str
    platform_number: str
    length_m: float = 400.0
    capacity: int = 1
    is_occupied: bool = False
    current_train_id: Optional[str] = None
    status: str = "AVAILABLE"
    has_overhead_catenary: bool = True
    accessibility_score: float = 1.0

class StationNode(BaseModel):
    id: str
    name: str
    code: str
    latitude: float
    longitude: float
    zone: str = "Central"
    passenger_capacity: int = 5000
    current_occupancy: int = 0
    status: str = "OPERATIONAL"
    platforms: Dict[str, PlatformElement] = Field(default_factory=dict)

class SignalElement(BaseModel):
    id: str
    track_id: str
    location_km: float = 0.0
    aspect: SignalAspect = SignalAspect.GREEN
    is_faulty: bool = False
    controlled_by_switch_id: Optional[str] = None

class SwitchElement(BaseModel):
    id: str
    junction_id: str
    state: SwitchState = SwitchState.NORMAL
    is_locked: bool = False
    locked_for_train_id: Optional[str] = None
    divergence_speed_kmh: float = 60.0

class JunctionNode(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    max_throughput_tph: int = 24
    switches: Dict[str, SwitchElement] = Field(default_factory=dict)
    connected_tracks: List[str] = Field(default_factory=list)

class TrackEdge(BaseModel):
    id: str
    name: str
    source_node: str
    target_node: str
    length_km: float
    max_speed_kmh: float = 160.0
    gradient_percent: float = 0.0
    electrified: bool = True
    track_type: str = "MAINLINE"  # MAINLINE, PASSING_LOOP, SIDING, HIGH_SPEED, TUNNEL, BRIDGE
    is_bidirectional: bool = False
    status: TrackStatus = TrackStatus.CLEAR
    current_train_ids: List[str] = Field(default_factory=list)
    speed_restriction_kmh: Optional[float] = None
    signals: List[SignalElement] = Field(default_factory=list)
    is_maintenance_closed: bool = False
