"""Simulation & Digital Twin models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    scenario_id = Column(String(50), nullable=True)
    status = Column(String(30), default="CREATED")  # CREATED, RUNNING, PAUSED, COMPLETED, STOPPED
    mode = Column(String(30), default="REALTIME")  # REALTIME, ACCELERATED, HISTORICAL, WHAT_IF
    time_acceleration = Column(Float, default=1.0)
    current_sim_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    total_trains = Column(Integer, default=0)
    active_conflicts = Column(Integer, default=0)
    resolved_conflicts = Column(Integer, default=0)
    average_delay_minutes = Column(Float, default=0.0)
    punctuality_percentage = Column(Float, default=100.0)
    total_energy_kwh = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SimulationEvent(Base):
    __tablename__ = "simulation_events"
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_run_id = Column(String(50), ForeignKey("simulation_runs.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    sim_time = Column(DateTime, nullable=False, index=True)
    entity_id = Column(String(50), nullable=True)  # Train ID, Track ID, etc.
    entity_type = Column(String(30), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Scenario(Base):
    __tablename__ = "scenarios"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    scenario_type = Column(String(50), default="CUSTOM")  # TRACK_CLOSURE, TRAIN_DELAY, SIGNAL_FAILURE, PASSENGER_SURGE, WEATHER
    parameters = Column(JSON, nullable=False)  # disruption details
    baseline_run_id = Column(String(50), nullable=True)
    optimized_run_id = Column(String(50), nullable=True)
    improvement_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
