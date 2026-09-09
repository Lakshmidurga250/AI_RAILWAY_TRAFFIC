"""Platform Manager and Dwell Time Engine."""
from typing import Dict, List, Optional
from simulation.network.elements import StationNode, PlatformElement
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class PlatformManager:
    """Manages station platform allocations and dwell calculations."""
    
    def __init__(self, stations: Dict[str, StationNode]):
        self.stations = stations

    def assign_platform(self, station_id: str, train_id: str, train_length_m: float, sim_time=None) -> Optional[PlatformElement]:
        """Find best available platform for arriving train."""
        station = self.stations.get(station_id)
        if not station:
            return None

        # Find compatible, unoccupied platform
        for platform in station.platforms.values():
            if not platform.is_occupied and platform.status == "AVAILABLE" and platform.length_m >= train_length_m:
                platform.is_occupied = True
                platform.current_train_id = train_id
                platform.status = "OCCUPIED"
                
                if sim_time:
                    event_bus.publish(SimEvent(
                        event_type=EventType.PLATFORM_ASSIGNED,
                        sim_time=sim_time,
                        entity_id=platform.id,
                        entity_type="PLATFORM",
                        payload={"station_id": station_id, "train_id": train_id, "platform_number": platform.platform_number}
                    ))
                return platform
        return None

    def release_platform(self, station_id: str, platform_id: str, train_id: str, sim_time=None):
        """Free platform upon train departure."""
        station = self.stations.get(station_id)
        if not station:
            return
        platform = station.platforms.get(platform_id)
        if platform and platform.current_train_id == train_id:
            platform.is_occupied = False
            platform.current_train_id = None
            platform.status = "AVAILABLE"
            
            if sim_time:
                event_bus.publish(SimEvent(
                    event_type=EventType.PLATFORM_RELEASED,
                    sim_time=sim_time,
                    entity_id=platform.id,
                    entity_type="PLATFORM",
                    payload={"station_id": station_id, "train_id": train_id}
                ))

    @staticmethod
    def calculate_dwell_seconds(passengers_on: int, passengers_off: int, num_doors: int = 16) -> int:
        """Calculate dynamic dwell time based on passenger exchange.
        
        Empirical railway rule:
        Dwell = Base door open/close time (20s) + (Total passenger movements / door rate)
        Average door rate: 1.2 passengers per door per second.
        """
        base_time = 25
        total_exchange = passengers_on + passengers_off
        flow_rate = num_doors * 1.1
        movement_time = total_exchange / max(1.0, flow_rate)
        return int(max(60, min(300, base_time + movement_time)))
