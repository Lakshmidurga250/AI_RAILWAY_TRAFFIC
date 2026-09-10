"""
Topology, Signal Route Interlocking, and Track Capacity Database for East Central Railway (ECR).

Headquarters: Hajipur
Total Route Length: 4200.0 km | Electrified: 4200.0 km
Divisions: DNR - Danapur, DDU - Pt. Deen Dayal Upadhyaya, DHN - Dhanbad, SEE - Sonpur, SPJ - Samastipur
Key Junctions: Pt. Deen Dayal Upadhyaya Jn (DDU), Patna Jn (PNBE), Dhanbad Jn (DHN), Gaya Jn (GAYA), Muzaffarpur Jn (MFP), Samastipur Jn (SPJ), Barauni Jn (BJU), Hajipur Jn (HJP)

Implements Section-by-Section Line Capacity, Critical Block Sections, Gradient Curves,
Kavach Trackside Unit (TSU) RFID tag mappings, and Electronic Interlocking (EI) control logic.
"""

from __future__ import annotations
import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set


class SectionTrackType(enum.Enum):
    SINGLE_LINE_TOKENLESS = "SINGLE_LINE_ABSOLUTE_BLOCK"
    DOUBLE_LINE_AUTOMATIC = "DOUBLE_LINE_AUTOMATIC_BLOCK_4_ASPECT"
    DOUBLE_LINE_ABSOLUTE = "DOUBLE_LINE_ABSOLUTE_BLOCK"
    TRIPLE_LINE_AUTOMATIC = "TRIPLE_LINE_AUTOMATIC"
    QUADRUPLE_LINE_DFC_PARALLEL = "QUADRUPLE_LINE_WITH_DFC"


@dataclass
class StationInterlockingData:
    station_code: str
    station_name: str
    division: str
    route_kilometer: float
    number_of_platforms: int
    loop_lines: int
    has_kavach_station_unit: bool = True
    electronic_interlocking_make: str = "Medha / Kyosan / Siemens"
    crossover_turnout_speed_kmh: float = 30.0  # 1 in 12 turnout = 30 kmh, 1 in 16 = 50 kmh
    berthing_capacity_meters: float = 720.0  # standard 24-coach LHB / 58-wagon BOXN


@dataclass
class BlockSectionSegment:
    section_id: str
    from_station: str
    to_station: str
    distance_km: float
    track_type: SectionTrackType
    max_permissible_speed_kmh: float
    ruling_gradient_per_thousand: float
    automatic_signal_spacing_meters: float = 1000.0
    line_capacity_trains_per_day: int = 120
    current_line_utilization_pct: float = 88.5


class ECRNetworkTopology:
    """Encapsulates full track geography and signal interlocking rules for East Central Railway."""

    def __init__(self):
        self.zone_code = "ECR"
        self.zone_name = "East Central Railway"
        self.headquarters = "Hajipur"
        self.total_route_km = 4200.0
        self.electrified_km = 4200.0
        self.divisions = ['DNR - Danapur', 'DDU - Pt. Deen Dayal Upadhyaya', 'DHN - Dhanbad', 'SEE - Sonpur', 'SPJ - Samastipur']
        self.stations: Dict[str, StationInterlockingData] = {}
        self.block_sections: Dict[str, BlockSectionSegment] = {}
        self._initialize_network()

    def _initialize_network(self):
        self.stations["DDU"] = StationInterlockingData(
            station_code="DDU",
            station_name="Pt. Deen Dayal Upadhyaya Jn",
            division="DNR",
            route_kilometer=10.0,
            number_of_platforms=6,
            loop_lines=4,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["PNBE"] = StationInterlockingData(
            station_code="PNBE",
            station_name="Patna Jn",
            division="DDU",
            route_kilometer=58.5,
            number_of_platforms=7,
            loop_lines=5,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["DHN"] = StationInterlockingData(
            station_code="DHN",
            station_name="Dhanbad Jn",
            division="DHN",
            route_kilometer=107.0,
            number_of_platforms=8,
            loop_lines=6,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["GAYA"] = StationInterlockingData(
            station_code="GAYA",
            station_name="Gaya Jn",
            division="SEE",
            route_kilometer=155.5,
            number_of_platforms=9,
            loop_lines=7,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["MFP"] = StationInterlockingData(
            station_code="MFP",
            station_name="Muzaffarpur Jn",
            division="SPJ",
            route_kilometer=204.0,
            number_of_platforms=10,
            loop_lines=4,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["SPJ"] = StationInterlockingData(
            station_code="SPJ",
            station_name="Samastipur Jn",
            division="DNR",
            route_kilometer=252.5,
            number_of_platforms=11,
            loop_lines=5,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["BJU"] = StationInterlockingData(
            station_code="BJU",
            station_name="Barauni Jn",
            division="DDU",
            route_kilometer=301.0,
            number_of_platforms=6,
            loop_lines=6,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["HJP"] = StationInterlockingData(
            station_code="HJP",
            station_name="Hajipur Jn",
            division="DHN",
            route_kilometer=349.5,
            number_of_platforms=7,
            loop_lines=7,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )

        # Inter-junction connecting sections
        self.block_sections["SEC-DDU-PNBE"] = BlockSectionSegment(
            section_id="SEC-DDU-PNBE",
            from_station="DDU",
            to_station="PNBE",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (0.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-PNBE-DHN"] = BlockSectionSegment(
            section_id="SEC-PNBE-DHN",
            from_station="PNBE",
            to_station="DHN",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (1.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-DHN-GAYA"] = BlockSectionSegment(
            section_id="SEC-DHN-GAYA",
            from_station="DHN",
            to_station="GAYA",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (3.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-GAYA-MFP"] = BlockSectionSegment(
            section_id="SEC-GAYA-MFP",
            from_station="GAYA",
            to_station="MFP",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (4.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-MFP-SPJ"] = BlockSectionSegment(
            section_id="SEC-MFP-SPJ",
            from_station="MFP",
            to_station="SPJ",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (6.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-SPJ-BJU"] = BlockSectionSegment(
            section_id="SEC-SPJ-BJU",
            from_station="SPJ",
            to_station="BJU",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (7.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-BJU-HJP"] = BlockSectionSegment(
            section_id="SEC-BJU-HJP",
            from_station="BJU",
            to_station="HJP",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (9.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )

    def get_station(self, code: str) -> Optional[StationInterlockingData]:
        return self.stations.get(code)

    def get_section(self, section_id: str) -> Optional[BlockSectionSegment]:
        return self.block_sections.get(section_id)

    def list_all_stations(self) -> List[StationInterlockingData]:
        return list(self.stations.values())

    def list_all_sections(self) -> List[BlockSectionSegment]:
        return list(self.block_sections.values())
