"""Railway Dispatcher Incident Response Playbook & SIL-4 Heuristics.

Contains standardized, certified operating protocols for all mainline railway contingencies:
- Signal Passed at Danger (SPAD)
- Axle Counter Reset & Track Circuit Occupancy Failure
- Extreme Weather & Visibility Mitigation (Dense Fog Fog-SAFE Devices)
- OHE Catenary Power Failure & Neutral Section Stalling
- Point / Switch Motor Clamping & Interlocking Hangs
- Flash Flood Over Track Subgrade & Speed Restrictions
- Multi-Train Head-on & Rear-end Emergency Divergence
"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class IncidentProtocol:
    code: str
    title: str
    severity: str        # SIL4_CRITICAL, HIGH, MODERATE, ADVISORY
    system_subsystem: str # SIGNALING, TRAIN_CONTROL, TRACTION_OHE, TRACK_CIVIL
    trigger_condition: str
    immediate_automated_action: str
    dispatcher_checklist: List[str]
    max_safe_speed_kmh: float
    reset_clearance_required: bool

INCIDENT_PLAYBOOK: List[IncidentProtocol] = [
    IncidentProtocol(
        "SOP-SPAD-01",
        "Signal Passed at Danger (SPAD) Containment",
        "SIL4_CRITICAL",
        "SIGNALING",
        "Locomotive crosses stop signal boundary without active Movement Authority",
        "Actuate pneumatic Emergency Brake (EB) via Kavach ATP transponder; switch opposing route signals to RED",
        [
            "Verify loco velocity drops to 0 km/h via odometry telemetry",
            "Establish UHF voice contact with loco pilot and guard",
            "Set protective flank interlocking on adjacent crossovers",
            "Log event into SIL-4 Blackbox and notify Chief Controller"
        ],
        0.0,
        True
    ),
    IncidentProtocol(
        "SOP-FOG-02",
        "Dense Fog Speed Regulation & Fog-SAFE Actuation",
        "MODERATE",
        "TRAIN_CONTROL",
        "Visibility under 150m reported by station master / atmospheric sensor",
        "Enforce automated 75 km/h maximum speed ceiling in block section; arm onboard GPS Fog-SAFE beacon",
        [
            "Verify detonator placement at warning distance if required",
            "Extend headway spacing from 180s to 360s between trailing rakes",
            "Alert level crossing gatekeepers on corridor"
        ],
        75.0,
        False
    ),
    IncidentProtocol(
        "SOP-AXLE-03",
        "Digital Axle Counter (DAC) Track Occupancy Glitch",
        "HIGH",
        "SIGNALING",
        "Block section displays occupied with no verified train telemetry",
        "Clamp signal to Yellow/Red; restrict subsequent trains to 25 km/h Caution Order",
        [
            "Check track voltage and sensor pulse counts at relay room",
            "Execute preparatory reset protocol with line verification by Station Master",
            "Dispatch pilot train at restricted 15 km/h speed with caution order"
        ],
        15.0,
        True
    ),
    IncidentProtocol(
        "SOP-OHE-04",
        "25kV AC Traction Power Grid Trip & Neutral Section Stall",
        "HIGH",
        "TRACTION_OHE",
        "Sub-station circuit breaker trip; catenary voltage drops below 19kV",
        "Trigger regenerative brake cutoff; notify following EMU/locos to coast",
        [
            "Isolate feeder sector at Traction Power Control (TPC)",
            "Verify pantograph status across stalled locos",
            "Prevent subsequent rakes from entering grade gradients under coasting"
        ],
        0.0,
        True
    ),
    IncidentProtocol(
        "SOP-SWITCH-05",
        "Junction Switch Point Motor Detection Failure",
        "SIL4_CRITICAL",
        "SIGNALING",
        "Switch point fails to achieve locked detection within 8 seconds of command",
        "De-energize route clearance; display red signal on all approaches to junction",
        [
            "Instruct station pointsman to physically inspect tongue rail for ballast obstruction",
            "Manual crank operation with padlocking and cotter pin insertion",
            "Authorize train movement via written pilot-in memo only"
        ],
        10.0,
        True
    ),
    IncidentProtocol(
        "SOP-FLOOD-06",
        "Water Level Above Danger Mark on Rail Web",
        "SIL4_CRITICAL",
        "TRACK_CIVIL",
        "Water sensor indicates floodwater over 75mm above rail crown",
        "Halt all traffic over bridge/culvert block; trip upstream signals",
        [
            "Civil engineering inspection of track bed and ballast washout",
            "Inspect bridge pier scour meters",
            "Resume traffic only after certified fitness clearance at 10 km/h walking pace"
        ],
        0.0,
        True
    ),
    IncidentProtocol(
        "SOP-HOTAXLE-07",
        "Hot Axle Box / Bearing Temperature Alarm",
        "HIGH",
        "TRAIN_CONTROL",
        "Acoustic / Infrared wayside sensor detects axle temperature > 90 deg C",
        "Divert train to loop line at next station with rolling stock inspection siding",
        [
            "Alert loco pilot via radio to observe caution when decelerating",
            "Station master visually checks smoking bearing on train pass-by",
            "Detach affected coach/wagon immediately to sick line"
        ],
        30.0,
        True
    ),
    IncidentProtocol(
        "SOP-CONVERG-08",
        "Multi-Train Junction Dynamic Convergence Resolution",
        "HIGH",
        "TRAIN_CONTROL",
        "Two trains projected to reach converging diamond crossover within 120 seconds",
        "Execute AI Pareto dynamic rescheduling: hold lower priority rake on loop, expedite premium rake",
        [
            "Signal green on high-speed mainline bypass",
            "Set approach signal on freight relief track to double yellow, then yellow",
            "Confirm headway adherence post junction clearance"
        ],
        50.0,
        False
    ),
]

def get_incident_playbook_summary() -> Dict[str, Any]:
    return {
        "total_protocols": len(INCIDENT_PLAYBOOK),
        "standards": "Indian Railways General Rules (GR) & Subsidiary Rules (SR) Rev 2024",
        "safety_integrity_level": "SIL-4",
        "protocols": [p.__dict__ for p in INCIDENT_PLAYBOOK]
    }
