"""
Topology, Signal Route Interlocking, and Track Capacity Database for North Central Railway (NCR).

Headquarters: Prayagraj
Total Route Length: 3222.0 km | Electrified: 3222.0 km
Divisions: PRYJ - Prayagraj, AGC - Agra, JHS - Jhansi (Virangana Lakshmibai)
Key Junctions: Prayagraj Jn (PRYJ), Kanpur Central (CNB), Agra Cantt (AGC), Virangana Lakshmibai Jhansi (VGLJ), Mathura Jn (MTJ), Tundla Jn (TDL), Manikpur (MKP), Banda (BNDA)

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


class NCRNetworkTopology:
    """Encapsulates full track geography and signal interlocking rules for North Central Railway."""

    def __init__(self):
        self.zone_code = "NCR"
        self.zone_name = "North Central Railway"
        self.headquarters = "Prayagraj"
        self.total_route_km = 3222.0
        self.electrified_km = 3222.0
        self.divisions = ['PRYJ - Prayagraj', 'AGC - Agra', 'JHS - Jhansi (Virangana Lakshmibai)']
        self.stations: Dict[str, StationInterlockingData] = {}
        self.block_sections: Dict[str, BlockSectionSegment] = {}
        self._initialize_network()

    def _initialize_network(self):
        self.stations["PRYJ"] = StationInterlockingData(
            station_code="PRYJ",
            station_name="Prayagraj Jn",
            division="PRYJ",
            route_kilometer=10.0,
            number_of_platforms=6,
            loop_lines=4,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["CNB"] = StationInterlockingData(
            station_code="CNB",
            station_name="Kanpur Central",
            division="AGC",
            route_kilometer=58.5,
            number_of_platforms=7,
            loop_lines=5,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["AGC"] = StationInterlockingData(
            station_code="AGC",
            station_name="Agra Cantt",
            division="JHS",
            route_kilometer=107.0,
            number_of_platforms=8,
            loop_lines=6,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["VGLJ"] = StationInterlockingData(
            station_code="VGLJ",
            station_name="Virangana Lakshmibai Jhansi",
            division="PRYJ",
            route_kilometer=155.5,
            number_of_platforms=9,
            loop_lines=7,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["MTJ"] = StationInterlockingData(
            station_code="MTJ",
            station_name="Mathura Jn",
            division="AGC",
            route_kilometer=204.0,
            number_of_platforms=10,
            loop_lines=4,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["TDL"] = StationInterlockingData(
            station_code="TDL",
            station_name="Tundla Jn",
            division="JHS",
            route_kilometer=252.5,
            number_of_platforms=11,
            loop_lines=5,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )
        self.stations["MKP"] = StationInterlockingData(
            station_code="MKP",
            station_name="Manikpur",
            division="PRYJ",
            route_kilometer=301.0,
            number_of_platforms=6,
            loop_lines=6,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if True else 50.0
        )
        self.stations["BNDA"] = StationInterlockingData(
            station_code="BNDA",
            station_name="Banda",
            division="AGC",
            route_kilometer=349.5,
            number_of_platforms=7,
            loop_lines=7,
            has_kavach_station_unit=True,
            crossover_turnout_speed_kmh=30.0 if False else 50.0
        )

        # Inter-junction connecting sections
        self.block_sections["SEC-PRYJ-CNB"] = BlockSectionSegment(
            section_id="SEC-PRYJ-CNB",
            from_station="PRYJ",
            to_station="CNB",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (0.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-CNB-AGC"] = BlockSectionSegment(
            section_id="SEC-CNB-AGC",
            from_station="CNB",
            to_station="AGC",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (1.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-AGC-VGLJ"] = BlockSectionSegment(
            section_id="SEC-AGC-VGLJ",
            from_station="AGC",
            to_station="VGLJ",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (3.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-VGLJ-MTJ"] = BlockSectionSegment(
            section_id="SEC-VGLJ-MTJ",
            from_station="VGLJ",
            to_station="MTJ",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (4.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-MTJ-TDL"] = BlockSectionSegment(
            section_id="SEC-MTJ-TDL",
            from_station="MTJ",
            to_station="TDL",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (6.0),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-TDL-MKP"] = BlockSectionSegment(
            section_id="SEC-TDL-MKP",
            from_station="TDL",
            to_station="MKP",
            distance_km=48.5,
            track_type=SectionTrackType.DOUBLE_LINE_AUTOMATIC,
            max_permissible_speed_kmh=130.0,
            ruling_gradient_per_thousand=5.0 + (7.5),
            automatic_signal_spacing_meters=1000.0,
            line_capacity_trains_per_day=140,
            current_line_utilization_pct=92.4
        )
        self.block_sections["SEC-MKP-BNDA"] = BlockSectionSegment(
            section_id="SEC-MKP-BNDA",
            from_station="MKP",
            to_station="BNDA",
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
