"""
Advanced Railway Timetabling Engine.

Implements:
- Periodic Timetable (Fahrplan) generation
- Cyclic/headway-based scheduling
- Conflict-free slot allocation
- Minimum headway computation
- Buffer time insertion
- Connection management (transfer guarantees)
- Capacity computation (UIC 406 method)
- Infrastructure occupation diagrams
- Time-distance diagrams
- Timetable stability analysis
- Rolling stock circulation (vehicle scheduling)
- Crew scheduling (driver allocation)
- Macro/micro timetable levels
- Supplement time management
- Train path allocation (slot booking)
"""

from optimization.timetabling.slot_allocator import SlotAllocator, TrainSlot, SlotConflict
from optimization.timetabling.headway_calculator import HeadwayCalculator, HeadwayResult
from optimization.timetabling.connection_manager import ConnectionManager, Connection, ConnectionState
from optimization.timetabling.capacity_analyzer import CapacityAnalyzer, LineCapacity, OccupationResult
from optimization.timetabling.path_optimizer import TimetablePathOptimizer, TrainPath, PathConflict
from optimization.timetabling.rolling_stock_scheduler import RollingStockScheduler, VehicleBlock, VehicleCirculation
from optimization.timetabling.timetable_generator import TimetableGenerator, TimetableConfig, GeneratedTimetable
from optimization.timetabling.stability_analyzer import StabilityAnalyzer, StabilityResult, DelayPropagation

__all__ = [
    "SlotAllocator", "TrainSlot", "SlotConflict",
    "HeadwayCalculator", "HeadwayResult",
    "ConnectionManager", "Connection", "ConnectionState",
    "CapacityAnalyzer", "LineCapacity", "OccupationResult",
    "TimetablePathOptimizer", "TrainPath", "PathConflict",
    "RollingStockScheduler", "VehicleBlock", "VehicleCirculation",
    "TimetableGenerator", "TimetableConfig", "GeneratedTimetable",
    "StabilityAnalyzer", "StabilityResult", "DelayPropagation",
]
