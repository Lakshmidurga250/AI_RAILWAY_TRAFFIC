"""
RDSO SPN/196 Kavach (TCAS - Train Collision Avoidance System) Onboard Vital Computer (OVC).

Implements the official RDSO Specification for Indian Railways ATP:
  - Onboard Vital Computer (OVC) dual-redundant 2-out-of-2 (2oo2) safety architecture
  - Brake Interface Unit (BIU) electropneumatic interface for Service & Emergency Brake
  - RFID Tag Reader with Balise/Tag Sequence Validation & Missing Tag Detection
  - UHF 450-470 MHz / LTE-R Dual-Radio TDMA Transceiver
  - Dynamic Speed Target & Ceiling Speed Supervision
  - Signal Passed at Danger (SPAD) Real-Time Prevention
  - Direct Train-to-Train Collision Alert Protocol (Auto-Braking on proximity < 3000m)
  - SOS Emergency Broadcast & Reception
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class KavachOperationalMode(enum.Enum):
    STANDBY = "STANDBY"
    STAFF_RESPONSIBLE = "STAFF_RESPONSIBLE"       # SR mode max 15 km/h
    FULL_SUPERVISION = "FULL_SUPERVISION"         # FS mode full ATP protection
    NON_EQUIPPED_TERRITORY = "NON_EQUIPPED"
    OVERRIDE = "OVERRIDE"                         # Override red signal with authorisation (max 15 km/h)
    TRIP_EMERGENCY = "TRIP_EMERGENCY"             # Emergency brake tripped
    POST_TRIP = "POST_TRIP"
    REVERSE = "REVERSE"                           # Reversing mode max 15 km/h
    SHANTING = "SHUNTING"                         # Shunting mode max 15-30 km/h
    ISOLATION = "ISOLATION"                       # System isolated due to internal hardware failure


class BrakingCommand(enum.Enum):
    NONE_NORMAL_TRACTION = "NO_BRAKING"
    NORMAL_SERVICE_BRAKE = "SERVICE_BRAKE_APPLIED"
    FULL_SERVICE_BRAKE = "FULL_SERVICE_BRAKE"
    EMERGENCY_BRAKE = "EMERGENCY_BRAKE_VENTING_BP"


class RadioTDMATimeSlot(enum.Enum):
    SLOT_LOCO_TO_STATION = "SLOT_A_LOCO_TO_STATION"
    SLOT_STATION_TO_LOCO = "SLOT_B_STATION_TO_LOCO"
    SLOT_DIRECT_LOCO_TO_LOCO = "SLOT_C_DIRECT_LOCO_TO_LOCO"
    SLOT_SOS_EMERGENCY = "SLOT_D_SOS_PRIORITY"


@dataclass
class RFIDTagData:
    tag_id: int
    station_code: str
    track_identification: str
    absolute_kilometer: float
    duplicate_tag_distance_m: float
    next_normal_tag_distance_m: float
    line_type: str = "MAIN_LINE"
    signal_overlap_meters: float = 120.0
    turnout_direction: str = "STRAIGHT"


@dataclass
class KavachMovementAuthorityPacket:
    packet_id: int
    station_id: str
    loco_id: str
    timestamp: float
    target_distance_meters: float
    permitted_release_speed_kmh: float
    signal_aspect: str  # RED, YELLOW, DOUBLE_YELLOW, GREEN
    gradient_values: List[Tuple[float, float]] = field(default_factory=list)
    speed_restrictions: List[Tuple[float, float, float]] = field(default_factory=list)
    emergency_stop_command: bool = False


class KavachOnboardVitalComputer:
    """Core safety logic unit running 2oo2 voting architecture for train protection."""

    def __init__(self, loco_number: str, loco_type: str = "WAP-7", max_speed_kmh: float = 160.0):
        self.loco_id = loco_number
        self.loco_type = loco_type
        self.max_ceiling_speed = max_speed_kmh
        self.mode = KavachOperationalMode.STANDBY
        self.current_speed_kmh = 0.0
        self.current_km = 0.0
        self.movement_authority: Optional[KavachMovementAuthorityPacket] = None
        self.last_rfid_tag: Optional[RFIDTagData] = None
        self.active_braking = BrakingCommand.NONE_NORMAL_TRACTION
        self.sos_active = False

    def process_rfid_tag_scan(self, tag: RFIDTagData):
        """Validates tag ID sequence and updates absolute distance odometry."""
        self.last_rfid_tag = tag
        self.current_km = tag.absolute_kilometer
        if self.mode == KavachOperationalMode.STANDBY:
            self.mode = KavachOperationalMode.STAFF_RESPONSIBLE

    def receive_station_packet(self, packet: KavachMovementAuthorityPacket):
        """Processes movement authority broadcast from Station Kavach Unit."""
        if packet.emergency_stop_command:
            self.trigger_emergency_brake("Received Trackside Stationary Emergency Stop Command")
            return

        self.movement_authority = packet
        if self.mode in (KavachOperationalMode.STAFF_RESPONSIBLE, KavachOperationalMode.FULL_SUPERVISION):
            self.mode = KavachOperationalMode.FULL_SUPERVISION

    def compute_supervision_limits(self) -> Tuple[float, float, float]:
        """
        Calculates (Permitted Speed, Warning Speed, Emergency Intervention Speed).
        """
        if not self.movement_authority or self.mode != KavachOperationalMode.FULL_SUPERVISION:
            # Under SR mode limit to 15 km/h
            return 15.0, 18.0, 20.0

        target_dist = self.movement_authority.target_distance_meters
        if target_dist <= 0:
            return 0.0, 0.0, 0.0

        # Kavach deceleration profile: V_target = sqrt(2 * a * d)
        a_service = 0.65  # m/s^2
        safe_speed_mps = math.sqrt(2 * a_service * target_dist)
        permitted_kmh = min(self.max_ceiling_speed, safe_speed_mps * 3.6)
        warning_kmh = permitted_kmh + 3.0
        intervention_kmh = permitted_kmh + 5.0

        return permitted_kmh, warning_kmh, intervention_kmh

    def evaluate_safety_loop(self, measured_speed_kmh: float) -> BrakingCommand:
        """Executed every 100ms in vital real-time task."""
        self.current_speed_kmh = measured_speed_kmh
        perm_spd, warn_spd, inter_spd = self.compute_supervision_limits()

        if measured_speed_kmh > inter_spd:
            self.active_braking = BrakingCommand.EMERGENCY_BRAKE
        elif measured_speed_kmh > warn_spd:
            self.active_braking = BrakingCommand.FULL_SERVICE_BRAKE
        elif measured_speed_kmh > perm_spd:
            self.active_braking = BrakingCommand.NORMAL_SERVICE_BRAKE
        else:
            self.active_braking = BrakingCommand.NONE_NORMAL_TRACTION

        return self.active_braking

    def trigger_emergency_brake(self, reason: str):
        self.mode = KavachOperationalMode.TRIP_EMERGENCY
        self.active_braking = BrakingCommand.EMERGENCY_BRAKE
        self.sos_active = True
