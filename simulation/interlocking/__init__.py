"""
Computer-Based Interlocking (CBI) subsystem.

Implements ERTMS/ETCS Level 2 compliant interlocking logic with:
- Route locking and release
- Approach locking
- Flank protection
- Point detection and locking
- Signal aspect control
- Petri-net formal verification
- Overlap management
- Dead-lock detection
- Interlocking table enforcement
"""

from simulation.interlocking.cbi_engine import CBIEngine, InterlockingState
from simulation.interlocking.route_controller import RouteController, Route, RouteState
from simulation.interlocking.point_controller import PointController, PointMachine, PointPosition
from simulation.interlocking.signal_controller import SignalController, SignalAspect, SignalState
from simulation.interlocking.petri_net import PetriNet, Place, Transition, Token, PetriNetVerifier
from simulation.interlocking.overlap_manager import OverlapManager, Overlap, OverlapState
from simulation.interlocking.flank_protection import FlankProtection, FlankElement, FlankLockState
from simulation.interlocking.deadlock_detector import DeadlockDetector, DeadlockGraph, DeadlockCycle
from simulation.interlocking.interlocking_table import InterlockingTable, TableEntry, ConflictMatrix

__all__ = [
    "CBIEngine", "InterlockingState",
    "RouteController", "Route", "RouteState",
    "PointController", "PointMachine", "PointPosition",
    "SignalController", "SignalAspect", "SignalState",
    "PetriNet", "Place", "Transition", "Token", "PetriNetVerifier",
    "OverlapManager", "Overlap", "OverlapState",
    "FlankProtection", "FlankElement", "FlankLockState",
    "DeadlockDetector", "DeadlockGraph", "DeadlockCycle",
    "InterlockingTable", "TableEntry", "ConflictMatrix",
]
