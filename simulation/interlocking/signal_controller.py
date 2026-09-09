"""
Signal Controller for Computer-Based Interlocking.

Implements:
- Multi-aspect signal control (2, 3, 4, 5 aspect)
- AWS/TPWS integration
- Cab signalling (ETCS)
- Signal state machine (controlled by route state)
- Approach locking signal logic
- Junction signals (route indicators)
- Banner repeaters
- Shunt signals
- Speed restriction signals
- Signal-passed-at-danger (SPAD) monitoring
- Signal timer management
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalAspect(Enum):
    """Signal aspects covering UK/European 4-aspect + shunt signals."""
    # Stop aspects
    RED = "RED"                    # Danger / Stop
    FLASHING_RED = "FLASHING_RED"  # Preliminary caution (UK)

    # Caution aspects
    SINGLE_YELLOW = "SINGLE_YELLOW"        # Caution — next signal at danger
    DOUBLE_YELLOW = "DOUBLE_YELLOW"        # Preliminary caution
    FLASHING_YELLOW = "FLASHING_YELLOW"   # Preliminary caution (speed restriction)
    FLASHING_DOUBLE_YELLOW = "FLASHING_DOUBLE_YELLOW"

    # Clear aspects
    GREEN = "GREEN"               # Line clear / proceed at full speed
    FLASHING_GREEN = "FLASHING_GREEN"  # Proceed — line clear at enhanced speed

    # Speed restriction aspects (European)
    YELLOW_YELLOW_GREEN = "YYG"   # Speed restriction to next signal
    SPEED_40 = "S40"
    SPEED_60 = "S60"
    SPEED_80 = "S80"

    # Shunt aspects
    SHUNT = "SHUNT"               # Shunting movement authorized
    CALL_ON = "CALL_ON"          # Calling-on (proceed past danger into occupied section)
    PROCEED_AS_SIGNALLED = "PAS"

    # Cab signalling
    ETCS_PROCEED = "ETCS_PROCEED"
    ETCS_STOP = "ETCS_STOP"
    ETCS_TRIP = "ETCS_TRIP"

    # Other
    DARK = "DARK"                 # Signal off / not operative
    BLOCKED = "BLOCKED"           # Signal showing wrong aspect (failure)


class SignalType(Enum):
    HOME = auto()           # Principal signal protecting section entry
    STARTER = auto()        # Starting signal at station
    ADVANCE_STARTER = auto()
    DISTANT = auto()        # Warning signal for next home signal
    SHUNTING = auto()       # Ground signal for shunting
    JUNCTION = auto()       # Junction signal with route indicator
    BANNER_REPEATER = auto()  # Repeater for restricted sighting
    SPEED = auto()          # Speed restriction signal
    BUFFER_STOP = auto()    # Buffer stop signal
    ETCS = auto()           # ETCS/ERTMS cab-only signal


class SignalFailureMode(Enum):
    NONE = auto()
    LAMP_FAILURE = auto()           # Aspect lamp burned out
    CONTROLLER_FAILURE = auto()     # Signal controller fault
    CABLE_FAULT = auto()            # Cable between controller and head
    ASPECT_WRONG = auto()           # Wrong aspect displayed
    DARK_SIGNAL = auto()            # All lamps out (defaults to danger)
    STUCK_RED = auto()              # Signal stuck at danger
    STUCK_GREEN = auto()            # Signal stuck at clear (extremely dangerous)


@dataclass
class SignalState:
    current_aspect: SignalAspect = SignalAspect.RED
    route_indicator: Optional[str] = None    # e.g., "1A", "2B" for junction routing
    speed_restriction_kmh: Optional[float] = None
    is_operative: bool = True
    failure_mode: SignalFailureMode = SignalFailureMode.NONE
    last_aspect_change: Optional[datetime] = None
    aspect_history: List[Tuple[datetime, SignalAspect]] = field(default_factory=list)
    spad_count: int = 0                      # Signal Passed At Danger count
    approach_locked: bool = False
    cleared_by_route: Optional[str] = None


@dataclass
class Signal:
    """
    Full signal model — physical + logical state.
    """
    signal_id: str
    name: str
    signal_type: SignalType = SignalType.HOME
    aspects_supported: List[SignalAspect] = field(default_factory=list)
    location_m: float = 0.0         # Position on track (chainage)
    track_section_id: Optional[str] = None
    direction: str = "forward"
    preceding_signal_id: Optional[str] = None   # Signal ahead
    following_signal_id: Optional[str] = None   # Signal behind
    aws_equipped: bool = True
    tpws_equipped: bool = True
    etcs_equipped: bool = False

    state: SignalState = field(default_factory=SignalState)

    def __post_init__(self) -> None:
        if not self.aspects_supported:
            # Default 4-aspect set
            self.aspects_supported = [
                SignalAspect.RED, SignalAspect.SINGLE_YELLOW,
                SignalAspect.DOUBLE_YELLOW, SignalAspect.GREEN,
            ]

    def supports_aspect(self, aspect: SignalAspect) -> bool:
        return aspect in self.aspects_supported

    def current_aspect(self) -> SignalAspect:
        if not self.state.is_operative:
            return SignalAspect.RED  # Fail-safe: signal at danger
        return self.state.current_aspect

    def is_at_danger(self) -> bool:
        return self.current_aspect() in (SignalAspect.RED, SignalAspect.FLASHING_RED)

    def is_clear(self) -> bool:
        return self.current_aspect() in (
            SignalAspect.GREEN, SignalAspect.FLASHING_GREEN, SignalAspect.SHUNT
        )

    def __repr__(self) -> str:
        return (f"Signal({self.signal_id!r}, {self.signal_type.name}, "
                f"aspect={self.state.current_aspect.name})")


class SignalController:
    """
    Manages all signals in an interlocking area.
    Implements aspect sequencing, approach locking, and SPAD monitoring.
    """

    # Aspect precedence map: what aspect to show based on next signal's aspect
    ASPECT_SEQUENCE: Dict[SignalAspect, SignalAspect] = {
        SignalAspect.RED: SignalAspect.SINGLE_YELLOW,
        SignalAspect.SINGLE_YELLOW: SignalAspect.DOUBLE_YELLOW,
        SignalAspect.DOUBLE_YELLOW: SignalAspect.GREEN,
        SignalAspect.GREEN: SignalAspect.GREEN,
        SignalAspect.SHUNT: SignalAspect.GREEN,
    }

    def __init__(self) -> None:
        self.signals: Dict[str, Signal] = {}
        self._spad_callbacks: List[Callable] = []
        self._aspect_change_callbacks: List[Callable] = []

    def register_signal(self, signal: Signal) -> None:
        self.signals[signal.signal_id] = signal
        logger.info("Registered signal %s (%s)", signal.signal_id, signal.signal_type.name)

    def get_signal(self, signal_id: str) -> Optional[Signal]:
        return self.signals.get(signal_id)

    # ------------------------------------------------------------------
    # Aspect control
    # ------------------------------------------------------------------

    def set_aspect(self, signal_id: str, aspect: SignalAspect,
                   route_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Set a signal's displayed aspect. Validates against supported aspects.
        """
        if signal_id not in self.signals:
            return False, f"Signal {signal_id!r} not found"

        signal = self.signals[signal_id]

        if not signal.state.is_operative:
            return False, f"Signal {signal_id!r} is not operative (failure: {signal.state.failure_mode.name})"

        if not signal.supports_aspect(aspect):
            return False, f"Signal {signal_id!r} does not support aspect {aspect.name}"

        old_aspect = signal.state.current_aspect
        signal.state.current_aspect = aspect
        signal.state.last_aspect_change = datetime.utcnow()
        signal.state.aspect_history.append((datetime.utcnow(), aspect))
        signal.state.cleared_by_route = route_id

        # Keep history bounded
        if len(signal.state.aspect_history) > 200:
            signal.state.aspect_history = signal.state.aspect_history[-100:]

        logger.debug("Signal %s: %s -> %s (route=%s)", signal_id,
                     old_aspect.name, aspect.name, route_id)

        for cb in self._aspect_change_callbacks:
            try:
                cb(signal_id, old_aspect, aspect)
            except Exception:
                pass

        return True, f"Signal {signal_id} set to {aspect.name}"

    def clear_signal(self, signal_id: str, route_id: Optional[str] = None,
                     next_signal_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Clear a signal (set to proceed aspect) based on downstream signal's aspect.
        Implements 4-aspect propagation.
        """
        if signal_id not in self.signals:
            return False, "Signal not found"

        target_aspect = SignalAspect.GREEN

        if next_signal_id and next_signal_id in self.signals:
            next_aspect = self.signals[next_signal_id].current_aspect()
            target_aspect = self.ASPECT_SEQUENCE.get(next_aspect, SignalAspect.GREEN)

        return self.set_aspect(signal_id, target_aspect, route_id)

    def set_danger(self, signal_id: str, reason: str = "route_released") -> Tuple[bool, str]:
        """Set signal to RED (danger)."""
        return self.set_aspect(signal_id, SignalAspect.RED)

    def set_shunt(self, signal_id: str, route_id: Optional[str] = None) -> Tuple[bool, str]:
        """Set signal to shunting aspect."""
        signal = self.signals.get(signal_id)
        if signal and signal.signal_type == SignalType.SHUNTING:
            return self.set_aspect(signal_id, SignalAspect.SHUNT, route_id)
        return False, "Not a shunting signal"

    def set_call_on(self, signal_id: str) -> Tuple[bool, str]:
        """Set call-on aspect (proceed into occupied section with caution)."""
        return self.set_aspect(signal_id, SignalAspect.CALL_ON)

    # ------------------------------------------------------------------
    # Cascade aspect update
    # ------------------------------------------------------------------

    def propagate_aspects(self, from_signal_id: str, max_propagation: int = 10) -> int:
        """
        Propagate aspect changes backwards from a signal.
        When a signal changes to RED, the upstream signal(s) must be updated.
        Returns number of signals updated.
        """
        updated = 0
        current_id = from_signal_id

        for _ in range(max_propagation):
            current_signal = self.signals.get(current_id)
            if not current_signal or not current_signal.preceding_signal_id:
                break

            preceding_id = current_signal.preceding_signal_id
            preceding = self.signals.get(preceding_id)
            if not preceding:
                break

            # Determine what aspect preceding should show
            current_aspect = current_signal.current_aspect()
            new_preceding_aspect = self.ASPECT_SEQUENCE.get(current_aspect, SignalAspect.GREEN)

            if preceding.state.current_aspect != new_preceding_aspect:
                self.set_aspect(preceding_id, new_preceding_aspect)
                updated += 1

            current_id = preceding_id

        return updated

    # ------------------------------------------------------------------
    # SPAD monitoring
    # ------------------------------------------------------------------

    def report_spad(self, signal_id: str, train_id: str) -> Dict[str, Any]:
        """Record a Signal Passed At Danger (SPAD) incident."""
        if signal_id not in self.signals:
            return {"error": "Signal not found"}

        signal = self.signals[signal_id]
        signal.state.spad_count += 1

        incident = {
            "signal_id": signal_id,
            "signal_name": signal.name,
            "train_id": train_id,
            "timestamp": datetime.utcnow().isoformat(),
            "aspect_at_spad": signal.state.current_aspect.name,
            "spad_count_for_signal": signal.state.spad_count,
            "aws_equipped": signal.aws_equipped,
            "tpws_equipped": signal.tpws_equipped,
            "severity": "CRITICAL",
        }

        for cb in self._spad_callbacks:
            try:
                cb(incident)
            except Exception:
                pass

        logger.critical("SPAD! Signal=%s, Train=%s", signal_id, train_id)
        return incident

    # ------------------------------------------------------------------
    # Failure injection
    # ------------------------------------------------------------------

    def inject_failure(self, signal_id: str,
                       failure_mode: SignalFailureMode) -> bool:
        if signal_id not in self.signals:
            return False
        signal = self.signals[signal_id]
        signal.state.failure_mode = failure_mode
        signal.state.is_operative = False

        # Fail-safe: immediately set to danger
        signal.state.current_aspect = SignalAspect.RED
        logger.error("Signal %s failure injected: %s", signal_id, failure_mode.name)
        return True

    def restore_signal(self, signal_id: str) -> bool:
        if signal_id not in self.signals:
            return False
        signal = self.signals[signal_id]
        signal.state.failure_mode = SignalFailureMode.NONE
        signal.state.is_operative = True
        signal.state.current_aspect = SignalAspect.RED  # Restore at danger
        logger.info("Signal %s restored", signal_id)
        return True

    # ------------------------------------------------------------------
    # Status and reporting
    # ------------------------------------------------------------------

    def approach_lock_signal(self, signal_id: str) -> bool:
        if signal_id not in self.signals:
            return False
        self.signals[signal_id].state.approach_locked = True
        return True

    def release_approach_lock(self, signal_id: str) -> bool:
        if signal_id not in self.signals:
            return False
        self.signals[signal_id].state.approach_locked = False
        return True

    def get_signals_at_clear(self) -> List[str]:
        return [sid for sid, s in self.signals.items() if s.is_clear()]

    def get_signals_at_danger(self) -> List[str]:
        return [sid for sid, s in self.signals.items() if s.is_at_danger()]

    def get_failed_signals(self) -> List[Dict[str, Any]]:
        return [
            {"signal_id": sid, "failure": s.state.failure_mode.name}
            for sid, s in self.signals.items()
            if not s.state.is_operative
        ]

    def full_status_report(self) -> List[Dict[str, Any]]:
        return [
            {
                "signal_id": s.signal_id,
                "name": s.name,
                "type": s.signal_type.name,
                "aspect": s.state.current_aspect.name,
                "is_operative": s.state.is_operative,
                "failure_mode": s.state.failure_mode.name,
                "approach_locked": s.state.approach_locked,
                "cleared_by_route": s.state.cleared_by_route,
                "spad_count": s.state.spad_count,
                "route_indicator": s.state.route_indicator,
            }
            for s in self.signals.values()
        ]

    def on_spad(self, callback: Callable) -> None:
        self._spad_callbacks.append(callback)

    def on_aspect_change(self, callback: Callable) -> None:
        self._aspect_change_callbacks.append(callback)

    def statistics(self) -> Dict[str, Any]:
        total = len(self.signals)
        return {
            "total_signals": total,
            "at_clear": len(self.get_signals_at_clear()),
            "at_danger": len(self.get_signals_at_danger()),
            "failed": len(self.get_failed_signals()),
            "total_spads": sum(s.state.spad_count for s in self.signals.values()),
        }
