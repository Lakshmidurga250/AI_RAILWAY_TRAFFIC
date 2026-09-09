"""Event Bus for Simulation and Digital Twin."""
import asyncio
from typing import Callable, List, Dict, Any, Awaitable
from simulation.events.event_types import SimEvent, EventType

class EventBus:
    def __init__(self, max_history: int = 10000):
        self.subscribers: Dict[EventType, List[Callable[[SimEvent], Any]]] = {}
        self.async_subscribers: Dict[EventType, List[Callable[[SimEvent], Awaitable[None]]]] = {}
        self.all_subscribers: List[Callable[[SimEvent], Any]] = []
        self.history: List[SimEvent] = []
        self.max_history = max_history

    def subscribe(self, event_type: EventType, callback: Callable[[SimEvent], Any]):
        """Register synchronous listener for a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable[[SimEvent], Any]):
        """Register listener for all events."""
        self.all_subscribers.append(callback)

    def subscribe_async(self, event_type: EventType, callback: Callable[[SimEvent], Awaitable[None]]):
        """Register asynchronous listener."""
        if event_type not in self.async_subscribers:
            self.async_subscribers[event_type] = []
        self.async_subscribers[event_type].append(callback)

    def publish(self, event: SimEvent):
        """Publish event to all registered synchronous subscribers and store in history."""
        self.history.append(event)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Notify specific type subscribers
        if event.event_type in self.subscribers:
            for cb in self.subscribers[event.event_type]:
                try:
                    cb(event)
                except Exception as e:
                    print(f"Error in event subscriber {cb}: {e}")

        # Notify wildcard subscribers
        for cb in self.all_subscribers:
            try:
                cb(event)
            except Exception as e:
                print(f"Error in wildcard subscriber: {e}")

    async def publish_async(self, event: SimEvent):
        """Publish event and await async subscribers."""
        self.publish(event)
        if event.event_type in self.async_subscribers:
            for cb in self.async_subscribers[event.event_type]:
                try:
                    await cb(event)
                except Exception as e:
                    print(f"Error in async subscriber: {e}")

    def get_history(self, limit: int = 100, event_type: EventType = None) -> List[SimEvent]:
        """Get recent event history, optionally filtered."""
        events = self.history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

    def clear(self):
        """Clear history."""
        self.history.clear()

event_bus = EventBus()
