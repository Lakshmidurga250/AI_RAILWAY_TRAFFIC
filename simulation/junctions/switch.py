"""Railway Switch and Junction Controller."""
from typing import Dict, Optional
from simulation.network.elements import SwitchElement, SwitchState, JunctionNode
from simulation.events.event_types import SimEvent, EventType
from simulation.events.event_bus import event_bus

class SwitchController:
    """Manages junction turnout switches and safety interlocking."""
    
    def __init__(self, junctions: Dict[str, JunctionNode]):
        self.junctions = junctions
        self.switches: Dict[str, SwitchElement] = {}
        for jct in junctions.values():
            for sw_id, sw in jct.switches.items():
                self.switches[sw_id] = sw

    def throw_switch(self, switch_id: str, new_state: SwitchState, train_id: Optional[str] = None, sim_time=None) -> bool:
        """Safely switch points if not locked by conflicting train."""
        sw = self.switches.get(switch_id)
        if not sw:
            return False
            
        if sw.is_locked and sw.locked_for_train_id != train_id:
            return False  # Locked by another train

        sw.state = new_state
        if train_id:
            sw.is_locked = True
            sw.locked_for_train_id = train_id

        if sim_time:
            event_bus.publish(SimEvent(
                event_type=EventType.SWITCH_THROWN,
                sim_time=sim_time,
                entity_id=switch_id,
                entity_type="SWITCH",
                payload={"new_state": new_state.value, "locked_for": train_id}
            ))
        return True

    def unlock_switch(self, switch_id: str, train_id: str):
        """Release switch lock after train completes traverse."""
        sw = self.switches.get(switch_id)
        if sw and sw.locked_for_train_id == train_id:
            sw.is_locked = False
            sw.locked_for_train_id = None
