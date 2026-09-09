"""Simulation Train Runtime Entity."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from simulation.network.elements import TrackEdge
from simulation.trains.dynamics import TrainDynamics
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class PlannedStop(BaseModel):
    station_id: str
    platform_id: Optional[str] = None
    stop_sequence: int
    scheduled_arrival: datetime
    scheduled_departure: datetime
    actual_arrival: Optional[datetime] = None
    actual_departure: Optional[datetime] = None
    dwell_duration_seconds: int = 120
    is_completed: bool = False

class SimulationTrain:
    """Active train agent in the simulation engine."""
    
    def __init__(
        self,
        train_id: str,
        train_number: str,
        name: str,
        train_type: str = "INTERCITY",
        length_m: float = 200.0,
        mass_tons: float = 450.0,
        max_speed_kmh: float = 160.0,
        acceleration_ms2: float = 0.8,
        braking_ms2: float = 1.0,
        passenger_capacity: int = 600,
        current_passengers: int = 250,
        priority: int = 5,
        route_tracks: Optional[List[TrackEdge]] = None,
        schedules: Optional[List[PlannedStop]] = None
    ):
        self.id = train_id
        self.train_number = train_number
        self.name = name
        self.train_type = train_type
        self.length_m = length_m
        self.mass_tons = mass_tons
        self.max_speed_kmh = max_speed_kmh
        self.acceleration_ms2 = acceleration_ms2
        self.braking_ms2 = braking_ms2
        self.passenger_capacity = passenger_capacity
        self.current_passengers = current_passengers
        self.priority = priority
        
        self.route_tracks: List[TrackEdge] = route_tracks or []
        self.current_track_index: int = 0
        self.distance_along_current_track_km: float = 0.0
        
        self.schedules: List[PlannedStop] = schedules or []
        self.current_stop_index: int = 0
        
        # State
        self.status: str = "SCHEDULED"  # SCHEDULED, RUNNING, DWELLING, DELAYED, STOPPED, COMPLETED
        self.current_speed_kmh: float = 0.0
        self.target_speed_kmh: float = 0.0
        self.current_delay_minutes: float = 0.0
        self.dwell_time_remaining_seconds: float = 0.0
        
        # Energy
        self.cumulative_energy_kwh: float = 0.0
        self.regenerated_energy_kwh: float = 0.0
        
        # Position Coordinates (for map)
        self.current_lat: Optional[float] = None
        self.current_lng: Optional[float] = None
        self.assigned_platform_id: Optional[str] = None

    @property
    def current_track(self) -> Optional[TrackEdge]:
        if 0 <= self.current_track_index < len(self.route_tracks):
            return self.route_tracks[self.current_track_index]
        return None

    def update_position_coords(self, node_positions: Dict[str, tuple]):
        """Interpolate current GPS coordinates based on track progress."""
        track = self.current_track
        if not track or track.length_km <= 0:
            return
            
        src_pos = node_positions.get(track.source_node)
        tgt_pos = node_positions.get(track.target_node)
        if src_pos and tgt_pos:
            ratio = min(1.0, max(0.0, self.distance_along_current_track_km / track.length_km))
            self.current_lat = src_pos[0] + (tgt_pos[0] - src_pos[0]) * ratio
            self.current_lng = src_pos[1] + (tgt_pos[1] - src_pos[1]) * ratio

    def check_departure_time(self, sim_time: datetime) -> bool:
        """Check if train should depart from initial terminal."""
        if not self.schedules or self.status != "SCHEDULED":
            return False
        first_stop = self.schedules[0]
        if sim_time >= first_stop.scheduled_departure:
            self.status = "RUNNING"
            self.target_speed_kmh = self.max_speed_kmh
            first_stop.actual_departure = sim_time
            if self.current_track:
                self.current_track.current_train_ids.append(self.id)
            event_bus.publish(SimEvent(
                event_type=EventType.TRAIN_DEPARTED,
                sim_time=sim_time,
                entity_id=self.id,
                entity_type="TRAIN",
                payload={"station_id": first_stop.station_id, "track_id": self.current_track.id if self.current_track else None}
            ))
            return True
        return False

    def step(self, dt_seconds: float, sim_time: datetime, node_positions: Dict[str, tuple]):
        """Advance train by dt_seconds in the simulation."""
        # 1. If scheduled, check departure
        if self.status == "SCHEDULED":
            self.check_departure_time(sim_time)
            return

        # 2. If completed, nothing to do
        if self.status == "COMPLETED":
            return

        # 3. If dwelling at platform
        if self.status == "DWELLING":
            self.dwell_time_remaining_seconds -= dt_seconds
            if self.dwell_time_remaining_seconds <= 0:
                # Dwell complete, ready to depart
                self.dwell_time_remaining_seconds = 0.0
                curr_stop = self.schedules[self.current_stop_index]
                curr_stop.actual_departure = sim_time
                curr_stop.is_completed = True
                self.current_stop_index += 1
                
                # Check if end of run
                if self.current_stop_index >= len(self.schedules):
                    self.status = "COMPLETED"
                    self.target_speed_kmh = 0.0
                    self.current_speed_kmh = 0.0
                    if self.current_track and self.id in self.current_track.current_train_ids:
                        self.current_track.current_train_ids.remove(self.id)
                    event_bus.publish(SimEvent(
                        event_type=EventType.TRAIN_ARRIVED,
                        sim_time=sim_time,
                        entity_id=self.id,
                        entity_type="TRAIN",
                        payload={"station_id": curr_stop.station_id, "is_final": True}
                    ))
                    return
                else:
                    self.status = "RUNNING"
                    self.target_speed_kmh = self.max_speed_kmh
                    event_bus.publish(SimEvent(
                        event_type=EventType.TRAIN_DEPARTED,
                        sim_time=sim_time,
                        entity_id=self.id,
                        entity_type="TRAIN",
                        payload={"station_id": curr_stop.station_id}
                    ))
            return

        # 4. Movement along tracks
        track = self.current_track
        if not track:
            self.status = "COMPLETED"
            return

        # Target speed is constrained by track speed limit and temporary restriction
        allowed_speed = track.speed_restriction_kmh or track.max_speed_kmh
        effective_target_spd = min(self.max_speed_kmh, allowed_speed)
        
        # Check upcoming station dwell deceleration
        next_station_stop = None
        if self.current_stop_index < len(self.schedules):
            cand_stop = self.schedules[self.current_stop_index]
            if cand_stop.station_id == track.target_node:
                next_station_stop = cand_stop

        # If approaching next station, compute required braking distance
        if next_station_stop:
            dist_to_station_km = max(0.0, track.length_km - self.distance_along_current_track_km)
            # Stopping distance: v^2 / (2 * a)
            curr_v_ms = (self.current_speed_kmh * 1000.0) / 3600.0
            braking_dist_km = ((curr_v_ms ** 2) / (2 * self.braking_ms2 * 1000.0)) * 1.3  # safety factor
            if dist_to_station_km <= braking_dist_km:
                effective_target_spd = 0.0

        # Step kinematics
        new_speed, dist_traveled_km, energy_kwh, regen_kwh = TrainDynamics.step_kinematics(
            current_speed_kmh=self.current_speed_kmh,
            target_speed_kmh=effective_target_spd,
            max_acceleration_ms2=self.acceleration_ms2,
            max_braking_ms2=self.braking_ms2,
            dt_seconds=dt_seconds,
            mass_tons=self.mass_tons,
            gradient_percent=track.gradient_percent
        )
        
        self.current_speed_kmh = new_speed
        self.distance_along_current_track_km += dist_traveled_km
        self.cumulative_energy_kwh += energy_kwh
        self.regenerated_energy_kwh += regen_kwh
        
        self.update_position_coords(node_positions)

        # Check if reached track end
        if self.distance_along_current_track_km >= track.length_km:
            # Release current track
            if self.id in track.current_train_ids:
                track.current_train_ids.remove(self.id)
                event_bus.publish(SimEvent(
                    event_type=EventType.TRACK_RELEASED,
                    sim_time=sim_time,
                    entity_id=track.id,
                    entity_type="TRACK",
                    payload={"train_id": self.id}
                ))

            # Did we arrive at a scheduled station?
            if next_station_stop:
                self.status = "DWELLING"
                self.current_speed_kmh = 0.0
                next_station_stop.actual_arrival = sim_time
                self.dwell_time_remaining_seconds = next_station_stop.dwell_duration_seconds
                
                # Calculate delay
                if next_station_stop.scheduled_arrival:
                    diff_sec = (sim_time - next_station_stop.scheduled_arrival).total_seconds()
                    self.current_delay_minutes = max(0.0, diff_sec / 60.0)
                    if self.current_delay_minutes > 2.0:
                        event_bus.publish(SimEvent(
                            event_type=EventType.TRAIN_DELAYED,
                            sim_time=sim_time,
                            entity_id=self.id,
                            entity_type="TRAIN",
                            payload={"delay_minutes": self.current_delay_minutes, "station": next_station_stop.station_id}
                        ))

                event_bus.publish(SimEvent(
                    event_type=EventType.TRAIN_ARRIVED,
                    sim_time=sim_time,
                    entity_id=self.id,
                    entity_type="TRAIN",
                    payload={"station_id": next_station_stop.station_id, "delay_min": self.current_delay_minutes}
                ))

            # Move to next track in route
            self.current_track_index += 1
            self.distance_along_current_track_km = 0.0
            
            if self.current_track_index < len(self.route_tracks):
                new_track = self.route_tracks[self.current_track_index]
                new_track.current_train_ids.append(self.id)
                event_bus.publish(SimEvent(
                    event_type=EventType.TRACK_OCCUPIED,
                    sim_time=sim_time,
                    entity_id=new_track.id,
                    entity_type="TRACK",
                    payload={"train_id": self.id}
                ))
            elif self.status != "DWELLING":
                self.status = "COMPLETED"
                self.current_speed_kmh = 0.0
