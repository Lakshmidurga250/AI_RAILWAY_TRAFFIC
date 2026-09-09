"""Discrete-Event and Continuous Step Railway Simulation Engine."""
import time
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from simulation.network.graph import RailwayNetwork
from simulation.network.loader import create_corridor_network
from simulation.trains.train import SimulationTrain, PlannedStop
from simulation.signals.signaling import SignalingSystem
from simulation.junctions.switch import SwitchController
from simulation.platforms.platform_manager import PlatformManager
from simulation.conflicts.detector import ConflictDetector, ConflictRecord
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class SimulationEngine:
    """Core simulation engine driving trains, signals, conflicts, and telemetry."""
    
    def __init__(self, network: Optional[RailwayNetwork] = None):
        self.network = network or create_corridor_network()
        self.signaling = SignalingSystem(self.network.tracks)
        self.switches = SwitchController(self.network.junctions)
        self.platforms = PlatformManager(self.network.stations)
        self.conflict_detector = ConflictDetector(self.network)
        
        self.trains: Dict[str, SimulationTrain] = {}
        self.sim_time = datetime.now(timezone.utc)
        self.time_acceleration = 1.0  # 1x, 5x, 10x, 30x, 60x
        self.is_running = False
        self.is_paused = False
        self.step_lock = threading.Lock()
        
        self.total_energy_kwh = 0.0
        self.resolved_conflicts_count = 0
        self._worker_thread: Optional[threading.Thread] = None

    def initialize_default_traffic(self):
        """Populate realistic train services across the network."""
        self.trains.clear()
        now = self.sim_time
        
        services = [
            # High-Speed Express: South -> Grand Central -> Airport -> Summit
            ("TR_101", "EXP-101", "Metropolis Bullet", "HIGH_SPEED", 200.0, 420.0, 200.0, 1.0, 1.1, 750, 480, 9,
             ["ST_SOUTH", "JCT_CENTRAL_W", "ST_CENTRAL", "ST_TECH", "JCT_BYPASS_E", "ST_AIRPORT", "JCT_AIRPORT_N", "ST_RIVER", "ST_VALLEY", "ST_SUMMIT"],
             now - timedelta(minutes=5), 180),
            
            # InterCity Down: Summit -> Riverdale -> Airport -> Central -> South
            ("TR_202", "IC-202", "Highland Shuttle", "INTERCITY", 180.0, 380.0, 160.0, 0.8, 1.0, 500, 320, 7,
             ["ST_SUMMIT", "ST_VALLEY", "ST_RIVER", "JCT_AIRPORT_N", "ST_AIRPORT", "JCT_BYPASS_E", "ST_TECH", "ST_CENTRAL", "JCT_CENTRAL_W", "ST_SOUTH"],
             now + timedelta(minutes=2), 120),
            
            # Commuter Shuttle: Harbor -> Central -> Metro -> North Central
            ("TR_303", "COM-303", "Harbor Commuter", "COMMUTER", 150.0, 300.0, 130.0, 0.9, 1.2, 800, 620, 5,
             ["ST_HARBOR", "JCT_CENTRAL_W", "ST_CENTRAL", "ST_METRO", "ST_NORTH"],
             now - timedelta(minutes=10), 90),

            # Regional Express: North Central -> Metro -> Central -> Harbor
            ("TR_404", "REG-404", "Northern Express", "REGIONAL", 160.0, 320.0, 140.0, 0.8, 1.0, 550, 310, 6,
             ["ST_NORTH", "ST_METRO", "ST_CENTRAL", "JCT_CENTRAL_W", "ST_HARBOR"],
             now - timedelta(minutes=3), 120),

            # Airport Express: Central Grand -> Tech -> Airport -> North Triangle
            ("TR_505", "APX-505", "SkyTrain Express", "HIGH_SPEED", 160.0, 350.0, 180.0, 1.1, 1.2, 450, 380, 8,
             ["ST_CENTRAL", "ST_TECH", "JCT_BYPASS_E", "ST_AIRPORT", "JCT_AIRPORT_N"],
             now + timedelta(minutes=6), 150),

            # Freight Courier: Harbor -> Relief Tunnel -> East Bypass -> Riverdale
            ("TR_606", "FRT-606", "Cross-City Heavy Cargo", "FREIGHT", 380.0, 1200.0, 90.0, 0.4, 0.6, 0, 0, 3,
             ["ST_HARBOR", "JCT_CENTRAL_W", "JCT_BYPASS_E", "ST_AIRPORT", "JCT_AIRPORT_N", "ST_RIVER"],
             now - timedelta(minutes=8), 0),
        ]

        for tid, tnum, name, ttype, length, mass, max_spd, acc, brk, cap, pax, prio, route_nodes, dep_time, dwell in services:
            # Build route tracks
            tracks = self.network.path_to_tracks(route_nodes)
            
            # Build planned stops for stations in route
            schedules = []
            stop_seq = 1
            curr_stop_time = dep_time
            for node_id in route_nodes:
                if node_id in self.network.stations:
                    arr_time = curr_stop_time if stop_seq > 1 else None
                    dep_time_stop = curr_stop_time + timedelta(seconds=dwell)
                    schedules.append(PlannedStop(
                        station_id=node_id,
                        platform_id=f"{node_id}_P1",
                        stop_sequence=stop_seq,
                        scheduled_arrival=arr_time or curr_stop_time,
                        scheduled_departure=dep_time_stop,
                        dwell_duration_seconds=dwell
                    ))
                    curr_stop_time = dep_time_stop + timedelta(minutes=8)  # expected run time to next
                    stop_seq += 1

            train = SimulationTrain(
                train_id=tid,
                train_number=tnum,
                name=name,
                train_type=ttype,
                length_m=length,
                mass_tons=mass,
                max_speed_kmh=max_spd,
                acceleration_ms2=acc,
                braking_ms2=brk,
                passenger_capacity=cap,
                current_passengers=pax,
                priority=prio,
                route_tracks=tracks,
                schedules=schedules
            )
            
            # Place train initially
            if tracks:
                train.current_track_index = 0
                train.update_position_coords(self.network.node_positions)
                
            self.trains[tid] = train
            event_bus.publish(SimEvent(
                event_type=EventType.TRAIN_CREATED,
                sim_time=self.sim_time,
                entity_id=tid,
                entity_type="TRAIN",
                payload={"train_number": tnum, "type": ttype}
            ))

    def step(self, dt_seconds: float = 1.0):
        """Execute one simulation step of dt_seconds."""
        with self.step_lock:
            scaled_dt = dt_seconds * self.time_acceleration
            self.sim_time += timedelta(seconds=scaled_dt)
            
            # 1. Advance train positions & kinematics
            for train in self.trains.values():
                train.step(scaled_dt, self.sim_time, self.network.node_positions)
                
            # 2. Update signaling aspects
            self.signaling.update_signals(self.sim_time)
            
            # 3. Detect conflicts
            active_train_list = [t for t in self.trains.values() if t.status in ("RUNNING", "DWELLING", "SCHEDULED")]
            self.conflict_detector.scan_conflicts(active_train_list, self.sim_time)
            
            # 4. Tally metrics
            self.total_energy_kwh = sum(t.cumulative_energy_kwh for t in self.trains.values())

    def start(self):
        """Start background simulation loop."""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
            self._worker_thread.start()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False

    def set_acceleration(self, factor: float):
        self.time_acceleration = max(0.1, min(120.0, factor))

    def _run_loop(self):
        """Internal background loop ticking at ~1Hz real-time."""
        while self.is_running:
            if not self.is_paused:
                self.step(dt_seconds=1.0)
            time.sleep(1.0)

    def get_status_summary(self) -> Dict[str, Any]:
        """Compute status report for APIs and dashboards."""
        with self.step_lock:
            active_trains = [t for t in self.trains.values() if t.status in ("RUNNING", "DWELLING")]
            delays = [t.current_delay_minutes for t in self.trains.values()]
            avg_delay = (sum(delays) / len(delays)) if delays else 0.0
            on_time_count = sum(1 for d in delays if d <= 3.0)
            punctuality = (on_time_count / len(delays) * 100.0) if delays else 100.0
            
            return {
                "id": "SIM_PRIMARY_RUN",
                "name": "Live Operational Network Simulation",
                "status": "PAUSED" if self.is_paused else ("RUNNING" if self.is_running else "STOPPED"),
                "mode": "REALTIME" if self.time_acceleration == 1.0 else "ACCELERATED",
                "time_acceleration": self.time_acceleration,
                "current_sim_time": self.sim_time.isoformat(),
                "start_time": self.sim_time.isoformat(),
                "total_trains": len(self.trains),
                "active_trains": len(active_trains),
                "active_conflicts": len(self.conflict_detector.active_conflicts),
                "resolved_conflicts": len(self.conflict_detector.resolved_conflicts),
                "average_delay_minutes": round(avg_delay, 2),
                "punctuality_percentage": round(punctuality, 1),
                "total_energy_kwh": round(self.total_energy_kwh, 2)
            }

# Singleton simulation engine instance
sim_engine = SimulationEngine()
sim_engine.initialize_default_traffic()
