"""
Timetable, Station Interlocking Routes, and Master Train Trajectories for Eastern Dedicated Freight Corridor (DFCCIL_E).
Contains detailed train runs (Vande Bharat, Rajdhani, Superfast, Freight, Passenger) with arrival/departure timings,
platform allocations, speed curves, signal aspect transitions, and block section occupancies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class StationStopSchedule:
    station_code: str
    arrival_time_min: int
    departure_time_min: int
    platform_number: int
    distance_from_origin_km: float
    scheduled_dwell_seconds: int
    loop_line_assigned: bool = False

@dataclass
class MasterTrainSchedule:
    train_number: str
    train_name: str
    train_type: str
    origin_station: str
    destination_station: str
    max_speed_kmh: float
    rakes_composition: str
    stops: List[StationStopSchedule] = field(default_factory=list)

class DFCCIL_EScheduleDatabase:
    """Master schedule repository for Eastern Dedicated Freight Corridor."""

    def __init__(self):
        self.zone_code = "DFCCIL_E"
        self.zone_name = "Eastern Dedicated Freight Corridor"
        self.trains: Dict[str, MasterTrainSchedule] = {}
        self._build_timetable()

    def _build_timetable(self):
        # Train 19792: DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19792 = MasterTrainSchedule(
            train_number="19792",
            train_name="DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Vande Bharat Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=160.0,
            rakes_composition="16-Car Vande Bharat EMU (Train 18)"
        )
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=360,
            departure_time_min=360,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=384,
            departure_time_min=386,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=416,
            departure_time_min=418,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=455,
            departure_time_min=460,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=483,
            departure_time_min=485,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=515,
            departure_time_min=517,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=553,
            departure_time_min=558,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=581,
            departure_time_min=583,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=612,
            departure_time_min=614,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19792.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=650,
            departure_time_min=650,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19792"] = t_19792

        # Train 19793: DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR
        t_19793 = MasterTrainSchedule(
            train_number="19793",
            train_name="DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Rajdhani Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-7 + 22 LHB Coaches (EOG/HOG)"
        )
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=400,
            departure_time_min=400,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=429,
            departure_time_min=431,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=468,
            departure_time_min=473,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=518,
            departure_time_min=520,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=548,
            departure_time_min=553,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19793.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=589,
            departure_time_min=589,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19793"] = t_19793

        # Train 19794: DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19794 = MasterTrainSchedule(
            train_number="19794",
            train_name="DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Shatabdi Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-5 + 16 LHB AC Chair Cars"
        )
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=440,
            departure_time_min=440,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=469,
            departure_time_min=471,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=508,
            departure_time_min=510,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=555,
            departure_time_min=560,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=588,
            departure_time_min=590,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=626,
            departure_time_min=628,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=672,
            departure_time_min=677,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=705,
            departure_time_min=707,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=743,
            departure_time_min=745,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19794.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=789,
            departure_time_min=789,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19794"] = t_19794

        # Train 19795: DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR
        t_19795 = MasterTrainSchedule(
            train_number="19795",
            train_name="DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Superfast Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=110.0,
            rakes_composition="WAP-7 + 24 LHB Coaches"
        )
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=480,
            departure_time_min=480,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=514,
            departure_time_min=516,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=560,
            departure_time_min=565,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=618,
            departure_time_min=620,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=654,
            departure_time_min=659,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19795.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=702,
            departure_time_min=702,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19795"] = t_19795

        # Train 19796: DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR
        t_19796 = MasterTrainSchedule(
            train_number="19796",
            train_name="DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Express Passenger",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=100.0,
            rakes_composition="WAP-4 + 22 ICF Coaches"
        )
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=520,
            departure_time_min=520,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=558,
            departure_time_min=560,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=608,
            departure_time_min=610,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=669,
            departure_time_min=674,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=711,
            departure_time_min=713,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=761,
            departure_time_min=763,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=821,
            departure_time_min=826,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=862,
            departure_time_min=864,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=911,
            departure_time_min=913,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19796.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=970,
            departure_time_min=970,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19796"] = t_19796

        # Train 19797: DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19797 = MasterTrainSchedule(
            train_number="19797",
            train_name="DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Container Double Stack Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=100.0,
            rakes_composition="WAG-9HC + 45 BLCA/BLCB Wagons"
        )
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=560,
            departure_time_min=560,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=598,
            departure_time_min=600,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=648,
            departure_time_min=653,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=712,
            departure_time_min=714,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=751,
            departure_time_min=756,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19797.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=804,
            departure_time_min=804,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19797"] = t_19797

        # Train 19798: DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR
        t_19798 = MasterTrainSchedule(
            train_number="19798",
            train_name="DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Heavy Coal Freight (BOXNHL)",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=75.0,
            rakes_composition="Twin WAG-12B + 58 BOXNHL Loaded Wagons"
        )
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=600,
            departure_time_min=600,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=651,
            departure_time_min=653,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=718,
            departure_time_min=720,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=798,
            departure_time_min=803,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=853,
            departure_time_min=855,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=919,
            departure_time_min=921,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=998,
            departure_time_min=1003,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1052,
            departure_time_min=1054,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1116,
            departure_time_min=1118,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19798.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1194,
            departure_time_min=1194,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19798"] = t_19798

        # Train 19799: DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19799 = MasterTrainSchedule(
            train_number="19799",
            train_name="DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="POL Petroleum Tanker Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=75.0,
            rakes_composition="WAG-9 + 50 BTPN Wagons"
        )
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=640,
            departure_time_min=640,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=691,
            departure_time_min=693,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=758,
            departure_time_min=763,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=841,
            departure_time_min=843,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=893,
            departure_time_min=898,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19799.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=962,
            departure_time_min=962,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19799"] = t_19799

        # Train 19800: DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19800 = MasterTrainSchedule(
            train_number="19800",
            train_name="DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Vande Bharat Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=160.0,
            rakes_composition="16-Car Vande Bharat EMU (Train 18)"
        )
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=680,
            departure_time_min=680,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=704,
            departure_time_min=706,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=736,
            departure_time_min=738,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=775,
            departure_time_min=780,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=803,
            departure_time_min=805,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=835,
            departure_time_min=837,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=873,
            departure_time_min=878,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=901,
            departure_time_min=903,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=932,
            departure_time_min=934,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19800.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=970,
            departure_time_min=970,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19800"] = t_19800

        # Train 19801: DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR
        t_19801 = MasterTrainSchedule(
            train_number="19801",
            train_name="DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Rajdhani Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-7 + 22 LHB Coaches (EOG/HOG)"
        )
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=720,
            departure_time_min=720,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=749,
            departure_time_min=751,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=788,
            departure_time_min=793,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=838,
            departure_time_min=840,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=868,
            departure_time_min=873,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19801.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=909,
            departure_time_min=909,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19801"] = t_19801

        # Train 19802: DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19802 = MasterTrainSchedule(
            train_number="19802",
            train_name="DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Shatabdi Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-5 + 16 LHB AC Chair Cars"
        )
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=760,
            departure_time_min=760,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=789,
            departure_time_min=791,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=828,
            departure_time_min=830,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=875,
            departure_time_min=880,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=908,
            departure_time_min=910,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=946,
            departure_time_min=948,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=992,
            departure_time_min=997,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1025,
            departure_time_min=1027,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1063,
            departure_time_min=1065,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19802.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1109,
            departure_time_min=1109,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19802"] = t_19802

        # Train 19803: DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR
        t_19803 = MasterTrainSchedule(
            train_number="19803",
            train_name="DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Superfast Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=110.0,
            rakes_composition="WAP-7 + 24 LHB Coaches"
        )
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=800,
            departure_time_min=800,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=834,
            departure_time_min=836,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=880,
            departure_time_min=885,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=938,
            departure_time_min=940,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=974,
            departure_time_min=979,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19803.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1022,
            departure_time_min=1022,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19803"] = t_19803

        # Train 19804: DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR
        t_19804 = MasterTrainSchedule(
            train_number="19804",
            train_name="DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Express Passenger",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=100.0,
            rakes_composition="WAP-4 + 22 ICF Coaches"
        )
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=840,
            departure_time_min=840,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=878,
            departure_time_min=880,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=928,
            departure_time_min=930,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=989,
            departure_time_min=994,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1031,
            departure_time_min=1033,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1081,
            departure_time_min=1083,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1141,
            departure_time_min=1146,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1182,
            departure_time_min=1184,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1231,
            departure_time_min=1233,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19804.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1290,
            departure_time_min=1290,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19804"] = t_19804

        # Train 19805: DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19805 = MasterTrainSchedule(
            train_number="19805",
            train_name="DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Container Double Stack Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=100.0,
            rakes_composition="WAG-9HC + 45 BLCA/BLCB Wagons"
        )
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=880,
            departure_time_min=880,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=918,
            departure_time_min=920,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=968,
            departure_time_min=973,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1032,
            departure_time_min=1034,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1071,
            departure_time_min=1076,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19805.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1124,
            departure_time_min=1124,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19805"] = t_19805

        # Train 19806: DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR
        t_19806 = MasterTrainSchedule(
            train_number="19806",
            train_name="DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Heavy Coal Freight (BOXNHL)",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=75.0,
            rakes_composition="Twin WAG-12B + 58 BOXNHL Loaded Wagons"
        )
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=920,
            departure_time_min=920,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=971,
            departure_time_min=973,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1038,
            departure_time_min=1040,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1118,
            departure_time_min=1123,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1173,
            departure_time_min=1175,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1239,
            departure_time_min=1241,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1318,
            departure_time_min=1323,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1372,
            departure_time_min=1374,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1436,
            departure_time_min=1438,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19806.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1514,
            departure_time_min=1514,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19806"] = t_19806

        # Train 19807: DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19807 = MasterTrainSchedule(
            train_number="19807",
            train_name="DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="POL Petroleum Tanker Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=75.0,
            rakes_composition="WAG-9 + 50 BTPN Wagons"
        )
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=960,
            departure_time_min=960,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1011,
            departure_time_min=1013,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1078,
            departure_time_min=1083,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1161,
            departure_time_min=1163,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1213,
            departure_time_min=1218,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19807.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1282,
            departure_time_min=1282,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19807"] = t_19807

        # Train 19808: DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19808 = MasterTrainSchedule(
            train_number="19808",
            train_name="DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Vande Bharat Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=160.0,
            rakes_composition="16-Car Vande Bharat EMU (Train 18)"
        )
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1000,
            departure_time_min=1000,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1024,
            departure_time_min=1026,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1056,
            departure_time_min=1058,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1095,
            departure_time_min=1100,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1123,
            departure_time_min=1125,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1155,
            departure_time_min=1157,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1193,
            departure_time_min=1198,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1221,
            departure_time_min=1223,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1252,
            departure_time_min=1254,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19808.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1290,
            departure_time_min=1290,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19808"] = t_19808

        # Train 19809: DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR
        t_19809 = MasterTrainSchedule(
            train_number="19809",
            train_name="DFCCIL_E Rajdhani Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Rajdhani Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-7 + 22 LHB Coaches (EOG/HOG)"
        )
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1040,
            departure_time_min=1040,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1069,
            departure_time_min=1071,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1108,
            departure_time_min=1113,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1158,
            departure_time_min=1160,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1188,
            departure_time_min=1193,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19809.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1229,
            departure_time_min=1229,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19809"] = t_19809

        # Train 19810: DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19810 = MasterTrainSchedule(
            train_number="19810",
            train_name="DFCCIL_E Shatabdi Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Shatabdi Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=130.0,
            rakes_composition="WAP-5 + 16 LHB AC Chair Cars"
        )
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1080,
            departure_time_min=1080,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1109,
            departure_time_min=1111,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1148,
            departure_time_min=1150,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1195,
            departure_time_min=1200,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1228,
            departure_time_min=1230,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1266,
            departure_time_min=1268,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1312,
            departure_time_min=1317,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1345,
            departure_time_min=1347,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1383,
            departure_time_min=1385,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19810.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1429,
            departure_time_min=1429,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19810"] = t_19810

        # Train 19811: DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR
        t_19811 = MasterTrainSchedule(
            train_number="19811",
            train_name="DFCCIL_E Superfast Express NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Superfast Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=110.0,
            rakes_composition="WAP-7 + 24 LHB Coaches"
        )
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1120,
            departure_time_min=1120,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1154,
            departure_time_min=1156,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1200,
            departure_time_min=1205,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1258,
            departure_time_min=1260,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1294,
            departure_time_min=1299,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19811.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1342,
            departure_time_min=1342,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19811"] = t_19811

        # Train 19812: DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR
        t_19812 = MasterTrainSchedule(
            train_number="19812",
            train_name="DFCCIL_E Express Passenger NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Express Passenger",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=100.0,
            rakes_composition="WAP-4 + 22 ICF Coaches"
        )
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1160,
            departure_time_min=1160,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1198,
            departure_time_min=1200,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1248,
            departure_time_min=1250,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1309,
            departure_time_min=1314,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1351,
            departure_time_min=1353,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1401,
            departure_time_min=1403,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1461,
            departure_time_min=1466,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1502,
            departure_time_min=1504,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1551,
            departure_time_min=1553,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19812.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1610,
            departure_time_min=1610,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19812"] = t_19812

        # Train 19813: DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19813 = MasterTrainSchedule(
            train_number="19813",
            train_name="DFCCIL_E Container Double Stack Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="Container Double Stack Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=100.0,
            rakes_composition="WAG-9HC + 45 BLCA/BLCB Wagons"
        )
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1200,
            departure_time_min=1200,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1238,
            departure_time_min=1240,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1288,
            departure_time_min=1293,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1352,
            departure_time_min=1354,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1391,
            departure_time_min=1396,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19813.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1444,
            departure_time_min=1444,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19813"] = t_19813

        # Train 19814: DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR
        t_19814 = MasterTrainSchedule(
            train_number="19814",
            train_name="DFCCIL_E Heavy Coal Freight (BOXNHL) NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Heavy Coal Freight (BOXNHL)",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=75.0,
            rakes_composition="Twin WAG-12B + 58 BOXNHL Loaded Wagons"
        )
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1240,
            departure_time_min=1240,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1291,
            departure_time_min=1293,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1358,
            departure_time_min=1360,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1438,
            departure_time_min=1443,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1493,
            departure_time_min=1495,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1559,
            departure_time_min=1561,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1638,
            departure_time_min=1643,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1692,
            departure_time_min=1694,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1756,
            departure_time_min=1758,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19814.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1834,
            departure_time_min=1834,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19814"] = t_19814

        # Train 19815: DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR
        t_19815 = MasterTrainSchedule(
            train_number="19815",
            train_name="DFCCIL_E POL Petroleum Tanker Freight NEW_SAHNEWAL-NEW_KANPUR",
            train_type="POL Petroleum Tanker Freight",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_KANPUR",
            max_speed_kmh=75.0,
            rakes_composition="WAG-9 + 50 BTPN Wagons"
        )
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1280,
            departure_time_min=1280,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1331,
            departure_time_min=1333,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1398,
            departure_time_min=1403,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1481,
            departure_time_min=1483,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1533,
            departure_time_min=1538,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19815.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1602,
            departure_time_min=1602,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        self.trains["19815"] = t_19815

        # Train 19816: DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR
        t_19816 = MasterTrainSchedule(
            train_number="19816",
            train_name="DFCCIL_E Vande Bharat Express NEW_SAHNEWAL-NEW_SONNAGAR",
            train_type="Vande Bharat Express",
            origin_station="NEW_SAHNEWAL",
            destination_station="NEW_SONNAGAR",
            max_speed_kmh=160.0,
            rakes_composition="16-Car Vande Bharat EMU (Train 18)"
        )
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_SAHNEWAL",
            arrival_time_min=1320,
            departure_time_min=1320,
            platform_number=1,
            distance_from_origin_km=0.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=True
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_SHAMBHU",
            arrival_time_min=1344,
            departure_time_min=1346,
            platform_number=2,
            distance_from_origin_km=48.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_KHURJA",
            arrival_time_min=1376,
            departure_time_min=1378,
            platform_number=3,
            distance_from_origin_km=109.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_TUNDLA",
            arrival_time_min=1415,
            departure_time_min=1420,
            platform_number=4,
            distance_from_origin_km=183.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_BHADAN",
            arrival_time_min=1443,
            departure_time_min=1445,
            platform_number=5,
            distance_from_origin_km=230.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_KANPUR",
            arrival_time_min=1475,
            departure_time_min=1477,
            platform_number=6,
            distance_from_origin_km=290.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=True
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_FATEHPUR",
            arrival_time_min=1513,
            departure_time_min=1518,
            platform_number=1,
            distance_from_origin_km=363.0,
            scheduled_dwell_seconds=300,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_PRAYAGRAJ",
            arrival_time_min=1541,
            departure_time_min=1543,
            platform_number=2,
            distance_from_origin_km=409.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_DDU",
            arrival_time_min=1572,
            departure_time_min=1574,
            platform_number=3,
            distance_from_origin_km=468.0,
            scheduled_dwell_seconds=120,
            loop_line_assigned=False
        ))
        t_19816.stops.append(StationStopSchedule(
            station_code="NEW_SONNAGAR",
            arrival_time_min=1610,
            departure_time_min=1610,
            platform_number=4,
            distance_from_origin_km=540.0,
            scheduled_dwell_seconds=0,
            loop_line_assigned=False
        ))
        self.trains["19816"] = t_19816

    def get_train(self, train_number: str) -> Optional[MasterTrainSchedule]:
        return self.trains.get(train_number)

    def list_all_trains(self) -> List[MasterTrainSchedule]:
        return list(self.trains.values())

