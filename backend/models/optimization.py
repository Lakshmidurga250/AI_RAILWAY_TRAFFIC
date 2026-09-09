"""Optimization Models: OptimizationRun, Results, and Explanations."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from backend.app.database import Base

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"
    
    id = Column(String(50), primary_key=True, index=True)
    optimization_type = Column(String(50), nullable=False)  # ROUTING, SCHEDULING, PLATFORM, RESCHEDULING, ENERGY, MULTI_OBJECTIVE
    algorithm = Column(String(50), nullable=False)  # DIJKSTRA, A_STAR, GENETIC, PSO, MIP, RL, HEURISTIC
    status = Column(String(30), default="COMPLETED")  # RUNNING, COMPLETED, FAILED
    execution_time_ms = Column(Float, default=0.0)
    
    # Baseline vs Optimized metrics
    baseline_delay_minutes = Column(Float, default=0.0)
    optimized_delay_minutes = Column(Float, default=0.0)
    delay_reduction_percentage = Column(Float, default=0.0)
    
    baseline_energy_kwh = Column(Float, default=0.0)
    optimized_energy_kwh = Column(Float, default=0.0)
    energy_savings_percentage = Column(Float, default=0.0)
    
    conflicts_resolved = Column(Integer, default=0)
    throughput_increase_percentage = Column(Float, default=0.0)
    
    input_parameters = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
