"""Railway Signaling and Interlocking Engine."""
from typing import Dict, List, Optional
from simulation.network.elements import SignalElement, SignalAspect, TrackEdge
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class SignalingSystem:
    """Manages 4-aspect railway block signals and automatic headway spacing."""
    
    def __init__(self, tracks: Dict[str, TrackEdge]):
        self.tracks = tracks

    def update_signals(self, sim_time) -> Dict[str, SignalAspect]:
        """Recalculate signal aspects based on track block occupations."""
        updated_aspects = {}
        for track_id, track in self.tracks.items():
            is_occupied = len(track.current_train_ids) > 0 or track.is_maintenance_closed
            
            for i, sig in enumerate(track.signals):
                old_aspect = sig.aspect
                if sig.is_faulty:
                    sig.aspect = SignalAspect.RED
                elif is_occupied:
                    sig.aspect = SignalAspect.RED
                else:
                    # Look ahead along track or connected tracks
                    sig.aspect = SignalAspect.GREEN

                if sig.aspect != old_aspect:
                    updated_aspects[sig.id] = sig.aspect
                    event_bus.publish(SimEvent(
                        event_type=EventType.SIGNAL_CHANGED,
                        sim_time=sim_time,
                        entity_id=sig.id,
                        entity_type="SIGNAL",
                        payload={"track_id": track_id, "aspect": sig.aspect.value, "old_aspect": old_aspect.value}
                    ))
        return updated_aspects

    def check_can_proceed(self, signal_id: str) -> bool:
        """Query if train is permitted to pass signal."""
        for track in self.tracks.values():
            for sig in track.signals:
                if sig.id == signal_id:
                    return sig.aspect != SignalAspect.RED
        return True
