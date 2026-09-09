"""Historical Replay Engine for Railway Network Simulation.

Enables scrubbing, timeline analysis, event playback, and post-incident investigation.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import copy

class ReplaySnapshot:
    """Immutable record of network and train state at a specific simulation instant."""
    def __init__(self, timestamp: datetime, step_index: int, state: Dict[str, Any]):
        self.timestamp = timestamp
        self.step_index = step_index
        self.state = state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "step_index": self.step_index,
            "train_count": len(self.state.get("trains", [])),
            "conflict_count": len(self.state.get("conflicts", [])),
            "active_delays_min": sum(t.get("delay_minutes", 0.0) for t in self.state.get("trains", []))
        }

class HistoricalReplayEngine:
    """Manages recording and replaying historical simulation states."""

    MAX_BUFFER_SNAPSHOTS = 1000

    def __init__(self):
        self.timeline: List[ReplaySnapshot] = []
        self.current_cursor: int = 0
        self.is_replaying: bool = False
        self.playback_speed: float = 1.0

    def record_step(self, sim_time: datetime, step_idx: int, live_snapshot: Dict[str, Any]):
        """Capture digital twin state for historical retrieval."""
        snapshot = ReplaySnapshot(
            timestamp=sim_time,
            step_index=step_idx,
            state=copy.deepcopy(live_snapshot)
        )
        self.timeline.append(snapshot)
        if len(self.timeline) > self.MAX_BUFFER_SNAPSHOTS:
            self.timeline.pop(0)
            if self.current_cursor > 0:
                self.current_cursor -= 1

    def get_timeline_summary(self) -> Dict[str, Any]:
        """Return range and point summaries of recorded replay frames."""
        if not self.timeline:
            return {
                "total_snapshots": 0,
                "start_time": None,
                "end_time": None,
                "cursor_index": 0,
                "frames": []
            }

        return {
            "total_snapshots": len(self.timeline),
            "start_time": self.timeline[0].timestamp.isoformat(),
            "end_time": self.timeline[-1].timestamp.isoformat(),
            "cursor_index": self.current_cursor,
            "frames": [s.to_dict() for s in self.timeline[-50:]]  # Latest 50 frames
        }

    def seek_to_index(self, index: int) -> Optional[Dict[str, Any]]:
        """Scrub cursor to a specific historical frame index."""
        if not self.timeline:
            return None
        self.current_cursor = max(0, min(len(self.timeline) - 1, index))
        return self.timeline[self.current_cursor].state

    def step_forward(self) -> Optional[Dict[str, Any]]:
        """Step one snapshot forward in history."""
        if not self.timeline or self.current_cursor >= len(self.timeline) - 1:
            return None
        self.current_cursor += 1
        return self.timeline[self.current_cursor].state

    def step_backward(self) -> Optional[Dict[str, Any]]:
        """Step one snapshot backward in history."""
        if not self.timeline or self.current_cursor <= 0:
            return None
        self.current_cursor -= 1
        return self.timeline[self.current_cursor].state

    def clear(self):
        self.timeline.clear()
        self.current_cursor = 0

historical_replayer = HistoricalReplayEngine()
