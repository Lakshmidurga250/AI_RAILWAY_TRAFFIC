"""Network Loader: Generates and populates realistic railway corridor networks."""
from simulation.network.elements import (
    StationNode, JunctionNode, TrackEdge, PlatformElement,
    SignalElement, SwitchElement, SignalAspect, TrackStatus, SwitchState
)
from simulation.network.graph import RailwayNetwork

def create_corridor_network() -> RailwayNetwork:
    """Creates a comprehensive, high-fidelity railway corridor network."""
    net = RailwayNetwork()
    
    # 1. Stations Definition
    station_configs = [
        ("ST_NORTH", "North Central Station", "NCR", 40.7128, -74.0060, "North", 12000, 6),
        ("ST_METRO", "Metro Boulevard", "MBL", 40.7300, -73.9850, "North", 8000, 4),
        ("ST_CENTRAL", "Grand Union Terminal", "GUT", 40.7580, -73.9855, "Central", 25000, 10),
        ("ST_TECH", "Silicon Point Hub", "SPH", 40.7850, -73.9680, "Central", 9500, 4),
        ("ST_AIRPORT", "International Airport Rail Link", "IAR", 40.8120, -73.9450, "East", 15000, 4),
        ("ST_RIVER", "Riverdale Junction Station", "RDJ", 40.8400, -73.9200, "East", 6000, 3),
        ("ST_VALLEY", "Valley Green", "VGN", 40.8750, -73.8900, "South", 4500, 2),
        ("ST_HARBOR", "Port Harbor Logistics Terminal", "PHL", 40.7000, -74.0300, "West", 7000, 4),
        ("ST_SUMMIT", "Highland Summit", "HLS", 40.9100, -73.8600, "North-East", 3500, 2),
        ("ST_SOUTH", "South Bay Terminal", "SBT", 40.6650, -73.9900, "South", 14000, 6),
    ]

    for st_id, name, code, lat, lng, zone, cap, num_platforms in station_configs:
        platforms = {}
        for p in range(1, num_platforms + 1):
            pid = f"{st_id}_P{p}"
            platforms[pid] = PlatformElement(
                id=pid,
                station_id=st_id,
                platform_number=str(p),
                length_m=420.0,
                capacity=1,
                is_occupied=False,
                status="AVAILABLE",
                has_overhead_catenary=True,
                accessibility_score=0.95
            )
        station = StationNode(
            id=st_id,
            name=name,
            code=code,
            latitude=lat,
            longitude=lng,
            zone=zone,
            passenger_capacity=cap,
            current_occupancy=int(cap * 0.25),
            status="OPERATIONAL",
            platforms=platforms
        )
        net.add_station(station)

    # 2. Junctions Definition
    junction_configs = [
        ("JCT_CENTRAL_W", "West Central Flying Junction", 40.7450, -74.0000, 32),
        ("JCT_AIRPORT_N", "Airport North Triangle", 40.8250, -73.9350, 28),
        ("JCT_SOUTH_DIV", "South Division Interchange", 40.6850, -74.0100, 24),
        ("JCT_BYPASS_E", "East Freight Bypass Junction", 40.7700, -73.9500, 20),
    ]

    for j_id, name, lat, lng, throughput in junction_configs:
        switches = {
            f"SW_{j_id}_1": SwitchElement(id=f"SW_{j_id}_1", junction_id=j_id, state=SwitchState.NORMAL),
            f"SW_{j_id}_2": SwitchElement(id=f"SW_{j_id}_2", junction_id=j_id, state=SwitchState.NORMAL),
        }
        junction = JunctionNode(
            id=j_id,
            name=name,
            latitude=lat,
            longitude=lng,
            max_throughput_tph=throughput,
            switches=switches,
            connected_tracks=[]
        )
        net.add_junction(junction)

    # 3. Track Segments (Double track mainline corridors + bypasses + sidings)
    track_defs = [
        # South to Harbor
        ("TRK_SB_HB_1", "South to Harbor Main", "ST_SOUTH", "ST_HARBOR", 6.2, 140.0, 0.2, "MAINLINE", True),
        # Harbor to Central Junction
        ("TRK_HB_JCW_1", "Harbor to West Jct", "ST_HARBOR", "JCT_CENTRAL_W", 4.5, 120.0, 0.0, "MAINLINE", True),
        # South to Central Junction
        ("TRK_SB_JCW_1", "South to West Jct Main", "ST_SOUTH", "JCT_CENTRAL_W", 7.8, 160.0, 0.1, "MAINLINE", True),
        # West Jct to Central Grand
        ("TRK_JCW_GUT_UP", "West Jct to Grand Union Up", "JCT_CENTRAL_W", "ST_CENTRAL", 3.2, 110.0, -0.1, "MAINLINE", False),
        ("TRK_GUT_JCW_DN", "Grand Union to West Jct Down", "ST_CENTRAL", "JCT_CENTRAL_W", 3.2, 110.0, 0.1, "MAINLINE", False),
        # Central Grand to Metro
        ("TRK_GUT_MBL_UP", "Grand Union to Metro Up", "ST_CENTRAL", "ST_METRO", 4.1, 130.0, 0.0, "MAINLINE", False),
        ("TRK_MBL_GUT_DN", "Metro to Grand Union Down", "ST_METRO", "ST_CENTRAL", 4.1, 130.0, 0.0, "MAINLINE", False),
        # Metro to North Central
        ("TRK_MBL_NCR_UP", "Metro to North Central Up", "ST_METRO", "ST_NORTH", 3.8, 140.0, 0.0, "MAINLINE", False),
        ("TRK_NCR_MBL_DN", "North Central to Metro Down", "ST_NORTH", "ST_METRO", 3.8, 140.0, 0.0, "MAINLINE", False),
        # Central Grand to Tech Point
        ("TRK_GUT_SPH_UP", "Grand Union to Silicon Pt Up", "ST_CENTRAL", "ST_TECH", 4.8, 150.0, 0.3, "MAINLINE", False),
        ("TRK_SPH_GUT_DN", "Silicon Pt to Grand Union Down", "ST_TECH", "ST_CENTRAL", 4.8, 150.0, -0.3, "MAINLINE", False),
        # Tech Point to East Bypass Junction
        ("TRK_SPH_JCE_1", "Tech Pt to East Bypass Jct", "ST_TECH", "JCT_BYPASS_E", 3.0, 140.0, 0.1, "MAINLINE", True),
        # East Bypass to Airport
        ("TRK_JCE_IAR_UP", "East Jct to Airport Link", "JCT_BYPASS_E", "ST_AIRPORT", 5.5, 200.0, 0.0, "HIGH_SPEED", False),
        ("TRK_IAR_JCE_DN", "Airport Link to East Jct", "ST_AIRPORT", "JCT_BYPASS_E", 5.5, 200.0, 0.0, "HIGH_SPEED", False),
        # Airport to Airport Triangle
        ("TRK_IAR_JCA_1", "Airport to North Triangle", "ST_AIRPORT", "JCT_AIRPORT_N", 2.6, 120.0, 0.0, "MAINLINE", True),
        # Airport Triangle to Riverdale
        ("TRK_JCA_RDJ_1", "Airport Jct to Riverdale", "JCT_AIRPORT_N", "ST_RIVER", 4.2, 160.0, -0.2, "MAINLINE", True),
        # Riverdale to Valley Green
        ("TRK_RDJ_VGN_1", "Riverdale to Valley Green", "ST_RIVER", "ST_VALLEY", 5.8, 160.0, 0.5, "MAINLINE", True),
        # Valley Green to Highland Summit (Mountain line with gradient)
        ("TRK_VGN_HLS_1", "Valley to Summit Alpine Line", "ST_VALLEY", "ST_SUMMIT", 6.5, 120.0, 1.8, "TUNNEL", True),
        # Alternative / Bypass routes: North Central directly to Airport Triangle
        ("TRK_NCR_JCA_BYPASS", "North Central Airport Express Bypass", "ST_NORTH", "JCT_AIRPORT_N", 8.4, 180.0, 0.0, "HIGH_SPEED", True),
        # Freight / Relief line: West Central Jct to East Bypass Jct
        ("TRK_JCW_JCE_RELIEF", "Cross-City Underground Relief Tunnel", "JCT_CENTRAL_W", "JCT_BYPASS_E", 6.0, 100.0, 0.0, "TUNNEL", True),
    ]

    for trk_id, name, src, tgt, length, max_spd, grad, t_type, bidir in track_defs:
        # Create signals along track
        signals = [
            SignalElement(id=f"SIG_{trk_id}_ENTRY", track_id=trk_id, location_km=0.1, aspect=SignalAspect.GREEN),
            SignalElement(id=f"SIG_{trk_id}_MID", track_id=trk_id, location_km=length * 0.5, aspect=SignalAspect.GREEN),
            SignalElement(id=f"SIG_{trk_id}_EXIT", track_id=trk_id, location_km=max(0.2, length - 0.2), aspect=SignalAspect.GREEN),
        ]
        track = TrackEdge(
            id=trk_id,
            name=name,
            source_node=src,
            target_node=tgt,
            length_km=length,
            max_speed_kmh=max_spd,
            gradient_percent=grad,
            electrified=True,
            track_type=t_type,
            is_bidirectional=bidir,
            status=TrackStatus.CLEAR,
            current_train_ids=[],
            signals=signals
        )
        net.add_track(track)

    return net
