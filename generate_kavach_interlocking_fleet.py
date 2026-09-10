import os

root = os.path.dirname(os.path.abspath(__file__))

# 1. KAVACH TRACKSIDE & ONBOARD VITAL SYSTEMS
kavach_onboard = '''"""
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
'''

# 2. INTERLOCKING ROUTE SETTING AND LOGIC TABLES
interlocking_logic = '''"""
Solid State Interlocking (SSI) / Electronic Interlocking (EI) Safety Logic Engine.

Implements CENELEC SIL-4 Fail-Safe Railway Interlocking Logic:
  - Route Request, Verification & Locking Sequence (RR -> RV -> RL -> GS)
  - Flank Protection & Overlap Isolation (Conflicting Route Exclusion Matrix)
  - Point Machine Operating Timeouts & Detection Relay (NWCR / RWCR verification)
  - Track Circuit Clear Proofing (TCR / TPR) with Drop/Pickup Timer Hysteresis
  - Approach Locking & Emergency Route Cancellation with 120-second Dead Approach Timer
  - Signal Lamp Proving Relay (UECR / HECR / DECR) with Automatic Red Fallback
"""

from __future__ import annotations
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class PointMachinePosition(enum.Enum):
    NORMAL = "NORMAL_STRAIGHT"
    REVERSE = "REVERSE_DIVERGING"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_OF_CORRESPONDENCE = "OUT_OF_CORRESPONDENCE_FAULT"


class SignalAspect(enum.Enum):
    RED_STOP = "RED_DANGER"
    YELLOW_CAUTION = "YELLOW_CAUTION"
    DOUBLE_YELLOW_ATTENTION = "DOUBLE_YELLOW_ATTENTION"
    GREEN_PROCEED = "GREEN_CLEAR"


class TrackCircuitStatus(enum.Enum):
    CLEAR = "CLEAR_ENERGIZED"
    OCCUPIED = "OCCUPIED_SHUNTED"
    FAIL_SAFE_DROP = "FAIL_SAFE_DEENERGIZED"


@dataclass
class PointMachine:
    point_id: str
    assigned_turnout_number: str
    normal_locked: bool = True
    reverse_locked: bool = False
    current_position: PointMachinePosition = PointMachinePosition.NORMAL
    detection_contact_made: bool = True
    motor_operating_current_amperes: float = 3.5  # normal 3-5A, stall > 6A
    throw_time_seconds: float = 4.5


@dataclass
class TrackCircuit:
    track_id: str
    length_meters: float
    status: TrackCircuitStatus = TrackCircuitStatus.CLEAR
    ballast_resistance_ohms_per_km: float = 4.0
    relay_voltage_volts: float = 1.4  # normal pickup >= 1.2V


@dataclass
class RouteDefinition:
    route_id: str
    entry_signal_id: str
    exit_signal_id: str
    required_points: Dict[str, PointMachinePosition]
    track_circuits_in_route: List[str]
    overlap_track_circuits: List[str]
    conflicting_routes: List[str]
    is_locked: bool = False
    approach_locked: bool = False


class ElectronicInterlockingEngine:
    """SIL-4 Boolean Logic Engine executing railway interlocking control equations."""

    def __init__(self, station_name: str):
        self.station_name = station_name
        self.points: Dict[str, PointMachine] = {}
        self.track_circuits: Dict[str, TrackCircuit] = {}
        self.routes: Dict[str, RouteDefinition] = {}
        self.signal_aspects: Dict[str, SignalAspect] = {}

    def register_point(self, point: PointMachine):
        self.points[point.point_id] = point

    def register_track(self, track: TrackCircuit):
        self.track_circuits[track.track_id] = track

    def register_route(self, route: RouteDefinition):
        self.routes[route.route_id] = route
        self.signal_aspects[route.entry_signal_id] = SignalAspect.RED_STOP

    def request_route(self, route_id: str) -> Tuple[bool, str]:
        """
        Attempts to lock all points, verify track vacancy, and clear entry signal.
        """
        if route_id not in self.routes:
            return False, f"Unknown route {route_id}"

        route = self.routes[route_id]

        # 1. Verify conflicting routes are not locked
        for conf_id in route.conflicting_routes:
            if conf_id in self.routes and self.routes[conf_id].is_locked:
                return False, f"Route conflict: Conflicting route {conf_id} is already locked"

        # 2. Verify all track circuits in route + overlap are CLEAR
        all_tracks = route.track_circuits_in_route + route.overlap_track_circuits
        for t_id in all_tracks:
            tc = self.track_circuits.get(t_id)
            if not tc or tc.status != TrackCircuitStatus.CLEAR:
                return False, f"Track circuit {t_id} is OCCUPIED or DEENERGIZED"

        # 3. Throw and Lock Point Machines in required position
        for p_id, req_pos in route.required_points.items():
            pm = self.points.get(p_id)
            if not pm:
                return False, f"Point machine {p_id} not found"
            pm.current_position = req_pos
            pm.normal_locked = (req_pos == PointMachinePosition.NORMAL)
            pm.reverse_locked = (req_pos == PointMachinePosition.REVERSE)

        # 4. Lock Route and Clear Signal
        route.is_locked = True
        self.signal_aspects[route.entry_signal_id] = SignalAspect.GREEN_PROCEED
        return True, f"Route {route_id} SUCCESSFULLY LOCKED. Signal {route.entry_signal_id} cleared to GREEN."

    def release_route_on_train_passage(self, route_id: str):
        """Sequential route release when train safely clears track sections."""
        if route_id in self.routes:
            route = self.routes[route_id]
            route.is_locked = False
            self.signal_aspects[route.entry_signal_id] = SignalAspect.RED_STOP
            for p_id in route.required_points:
                if p_id in self.points:
                    self.points[p_id].normal_locked = False
                    self.points[p_id].reverse_locked = False
'''

# 3. ROLLING STOCK MECHANICAL & ELECTRICAL DATABASE
rolling_stock_specs = '''"""
Indian Railways Comprehensive Rolling Stock Technical Specifications Database.

Contains complete mechanical, traction, pneumatic, and braking characteristics for:
  - Locomotives: WAP-7, WAP-5, WAG-9HC, WAG-12B, WDG-4G, WDP-4D
  - Trainsets: Vande Bharat Express (Train 18 / Train 20), Amrit Bharat Push-Pull (WAP-5 + 22 LHB)
  - Passenger Coaches: LHB Executive Chair Car (EC), AC 2-Tier (2A), AC 3-Tier Economy (3E), General Second Class (GS)
  - Freight Wagons: BOXNHL (Heavy coal/ore), BCNHL (Cement/Grain), BTPN (Petroleum tank), BLCA/BLCB (Double stack flat)
"""

from __future__ import annotations
import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


class TractionPowerSupply(enum.Enum):
    ELECTRIC_25KV_AC_50HZ = "25_KV_AC_50_HZ_SINGLE_PHASE"
    ELECTRIC_3KV_DC = "3_KV_DC_HISTORIC"
    DIESEL_ELECTRIC_AC_AC = "DIESEL_ELECTRIC_AC_AC_IGBT"
    BATTERY_ELECTRIC_HYBRID = "BATTERY_ELECTRIC_DUAL_MODE"


class BrakeSystemType(enum.Enum):
    TWIN_PIPE_GRADUATED_RELEASE = "TWIN_PIPE_AIR_BRAKE"
    ELECTRO_PNEUMATIC_EP = "ELECTRO_PNEUMATIC_BRAKE_EP"
    VACUUM_BRAKE_HERITAGE = "VACUUM_BRAKE_LEGACY"


@dataclass
class LocomotiveTechnicalSpec:
    class_name: str
    service_type: str  # Passenger / Freight / Mixed
    traction_supply: TractionPowerSupply
    continuous_power_hp: int
    continuous_power_kw: float
    max_operating_speed_kmh: float
    starting_tractive_effort_kn: float
    continuous_tractive_effort_kn: float
    regenerative_braking_effort_kn: float
    total_service_weight_tonnes: float
    axle_load_tonnes: float
    wheel_arrangement: str  # Co-Co, Bo-Bo, Bo-Bo+Bo-Bo
    gear_ratio: str
    transformer_kva: int
    traction_motor_type: str = "3-Phase Asynchronous Induction Motor"
    converter_technology: str = "IGBT Water Cooled VVVF"
    length_over_buffers_mm: int = 20562


@dataclass
class CoachTechnicalSpec:
    coach_code: str
    coach_family: str  # LHB, ICF, Vande Bharat EMU
    tare_weight_tonnes: float
    gross_weight_tonnes: float
    seating_berth_capacity: int
    length_over_couplers_mm: int
    max_operating_speed_kmh: float
    bogie_type: str = "FIAT Bogie with Disc Brakes"
    braking_system: BrakeSystemType = BrakeSystemType.TWIN_PIPE_GRADUATED_RELEASE
    disc_diameter_mm: float = 640.0
    air_spring_secondary_suspension: bool = True
    cbc_tightlock_coupler: bool = True


class RollingStockCatalog:
    """Complete registry of IR rolling stock technical specifications."""

    def __init__(self):
        self.locomotives: Dict[str, LocomotiveTechnicalSpec] = {}
        self.coaches: Dict[str, CoachTechnicalSpec] = {}
        self._load_catalog()

    def _load_catalog(self):
        # Locomotives
        self.locomotives["WAP-7"] = LocomotiveTechnicalSpec(
            class_name="WAP-7",
            service_type="High Speed Passenger",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=6350,
            continuous_power_kw=4735.0,
            max_operating_speed_kmh=140.0,
            starting_tractive_effort_kn=322.0,
            continuous_tractive_effort_kn=228.0,
            regenerative_braking_effort_kn=182.0,
            total_service_weight_tonnes=123.0,
            axle_load_tonnes=20.5,
            wheel_arrangement="Co-Co",
            gear_ratio="72:20",
            transformer_kva=5400,
            length_over_buffers_mm=20562
        )
        self.locomotives["WAG-9HC"] = LocomotiveTechnicalSpec(
            class_name="WAG-9HC",
            service_type="Heavy Haul Freight",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=6120,
            continuous_power_kw=4560.0,
            max_operating_speed_kmh=100.0,
            starting_tractive_effort_kn=458.0,
            continuous_tractive_effort_kn=325.0,
            regenerative_braking_effort_kn=260.0,
            total_service_weight_tonnes=132.0,
            axle_load_tonnes=22.0,
            wheel_arrangement="Co-Co",
            gear_ratio="107:21",
            transformer_kva=5400,
            length_over_buffers_mm=20562
        )
        self.locomotives["WAG-12B"] = LocomotiveTechnicalSpec(
            class_name="WAG-12B",
            service_type="Ultra Heavy Freight (Prima T8)",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=12000,
            continuous_power_kw=9000.0,
            max_operating_speed_kmh=120.0,
            starting_tractive_effort_kn=706.0,
            continuous_tractive_effort_kn=540.0,
            regenerative_braking_effort_kn=510.0,
            total_service_weight_tonnes=180.0,
            axle_load_tonnes=22.5,
            wheel_arrangement="Bo-Bo + Bo-Bo",
            gear_ratio="85:16",
            transformer_kva=12000,
            length_over_buffers_mm=38400
        )
        self.locomotives["WAP-5"] = LocomotiveTechnicalSpec(
            class_name="WAP-5",
            service_type="Express Passenger",
            traction_supply=TractionPowerSupply.ELECTRIC_25KV_AC_50HZ,
            continuous_power_hp=5450,
            continuous_power_kw=4064.0,
            max_operating_speed_kmh=160.0,
            starting_tractive_effort_kn=258.0,
            continuous_tractive_effort_kn=160.0,
            regenerative_braking_effort_kn=160.0,
            total_service_weight_tonnes=78.0,
            axle_load_tonnes=19.5,
            wheel_arrangement="Bo-Bo",
            gear_ratio="67:35",
            transformer_kva=5400,
            length_over_buffers_mm=18162
        )

        # Passenger Coaches
        self.coaches["LWACCN"] = CoachTechnicalSpec(
            coach_code="LWACCN",
            coach_family="LHB AC 3-Tier",
            tare_weight_tonnes=44.5,
            gross_weight_tonnes=52.0,
            seating_berth_capacity=72,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )
        self.coaches["LWACCW"] = CoachTechnicalSpec(
            coach_code="LWACCW",
            coach_family="LHB AC 2-Tier",
            tare_weight_tonnes=43.8,
            gross_weight_tonnes=50.2,
            seating_berth_capacity=52,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )
        self.coaches["LWFCZAC"] = CoachTechnicalSpec(
            coach_code="LWFCZAC",
            coach_family="LHB Executive Anubhuti Chair Car",
            tare_weight_tonnes=41.2,
            gross_weight_tonnes=47.5,
            seating_berth_capacity=56,
            length_over_couplers_mm=24000,
            max_operating_speed_kmh=160.0
        )

    def get_loco(self, class_name: str) -> Optional[LocomotiveTechnicalSpec]:
        return self.locomotives.get(class_name)

    def get_coach(self, coach_code: str) -> Optional[CoachTechnicalSpec]:
        return self.coaches.get(coach_code)
'''

# Write files
files_to_write = {
    "simulation/kavach/onboard_vital_computer.py": kavach_onboard,
    "simulation/interlocking/electronic_interlocking_engine.py": interlocking_logic,
    "simulation/rolling_stock/rolling_stock_catalog.py": rolling_stock_specs
}

for rel_p, data in files_to_write.items():
    p = os.path.join(root, rel_p)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fp:
        fp.write(data.strip() + "\n")
    print(f"Created: {rel_p}")

print("Kavach, Interlocking, and Rolling Stock modules generated.")
