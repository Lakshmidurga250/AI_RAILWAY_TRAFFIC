"""Train models: Train, Schedule, Route, Position, Telemetry, TrainEvent."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Train(Base):
    __tablename__ = "trains"
    
    id = Column(String(50), primary_key=True, index=True)
    train_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    train_type = Column(String(30), default="INTERCITY")  # HIGH_SPEED, INTERCITY, REGIONAL, FREIGHT, COMMUTER
    origin_station_id = Column(String(50), ForeignKey("stations.id"), nullable=False)
    destination_station_id = Column(String(50), ForeignKey("stations.id"), nullable=False)
    
    # Kinematics & Physical specs
    length_m = Column(Float, default=200.0)
    weight_tons = Column(Float, default=450.0)
    max_speed_kmh = Column(Float, default=160.0)
    acceleration_ms2 = Column(Float, default=0.8)
    braking_ms2 = Column(Float, default=1.0)
    regenerative_braking_eff = Column(Float, default=0.35)  # 35% regen efficiency
    
    # Capacity & Load
    passenger_capacity = Column(Integer, default=600)
    current_passengers = Column(Integer, default=0)
    priority = Column(Integer, default=5)  # 1 (lowest) to 10 (highest / emergency)
    
    # Operational Status
    status = Column(String(30), default="SCHEDULED")  # SCHEDULED, RUNNING, DWELLING, DELAYED, STOPPED, COMPLETED, CANCELLED
    current_speed_kmh = Column(Float, default=0.0)
    current_track_id = Column(String(50), nullable=True)
    current_platform_id = Column(String(50), nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Timing & Delays
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    estimated_departure = Column(DateTime, nullable=True)
    estimated_arrival = Column(DateTime, nullable=True)
    actual_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    current_delay_minutes = Column(Float, default=0.0)
    
    # Energy
    cumulative_energy_kwh = Column(Float, default=0.0)
    regenerated_energy_kwh = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    schedules = relationship("ScheduleStop", back_populates="train", cascade="all, delete-orphan")
    telemetry_records = relationship("TrainTelemetry", back_populates="train", cascade="all, delete-orphan")
    events = relationship("TrainEvent", back_populates="train", cascade="all, delete-orphan")
    status_history = relationship("TrainStatusHistory", back_populates="train", cascade="all, delete-orphan")
    positions = relationship("TrainPosition", back_populates="train", cascade="all, delete-orphan")

class ScheduleStop(Base):
    __tablename__ = "schedule_stops"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id"), nullable=False, index=True)
    station_id = Column(String(50), ForeignKey("stations.id"), nullable=False)
    platform_id = Column(String(50), nullable=True)
    stop_sequence = Column(Integer, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=True)
    scheduled_departure = Column(DateTime, nullable=True)
    actual_arrival = Column(DateTime, nullable=True)
    actual_departure = Column(DateTime, nullable=True)
    dwell_duration_seconds = Column(Integer, default=120)
    status = Column(String(30), default="PENDING")  # PENDING, ARRIVED, DEPARTED, SKIPPED
    
    train = relationship("Train", back_populates="schedules")

class TrainTelemetry(Base):
    __tablename__ = "train_telemetry"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    speed_kmh = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    current_track_id = Column(String(50), nullable=True)
    distance_along_track_km = Column(Float, default=0.0)
    throttle_percentage = Column(Float, default=0.0)
    brake_percentage = Column(Float, default=0.0)
    power_draw_kw = Column(Float, default=0.0)
    current_delay_min = Column(Float, default=0.0)
    passenger_count = Column(Integer, default=0)
    
    train = relationship("Train", back_populates="telemetry_records")

class TrainEvent(Base):
    __tablename__ = "train_events"
    
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # TRAIN_DEPARTED, TRAIN_ARRIVED, TRAIN_DELAYED, etc.
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    location_node = Column(String(50), nullable=True)
    details = Column(JSON, nullable=True)
    
    train = relationship("Train", back_populates="events")

class TrainType(Base):
    __tablename__ = "train_types"

    code = Column(String(30), primary_key=True, index=True)  # HIGH_SPEED, INTERCITY, REGIONAL, FREIGHT, COMMUTER
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    default_max_speed_kmh = Column(Float, default=160.0)
    default_acceleration_ms2 = Column(Float, default=0.8)
    default_braking_ms2 = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TrainCategory(Base):
    __tablename__ = "train_categories"

    code = Column(String(30), primary_key=True, index=True)  # PASSENGER_EXPRESS, FREIGHT_BULK, etc.
    name = Column(String(100), nullable=False)
    default_priority = Column(Integer, default=5)
    is_passenger = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class TrainStatusHistory(Base):
    __tablename__ = "train_status_history"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False, index=True)
    reason = Column(String(255), nullable=True)
    delay_at_time_min = Column(Float, default=0.0)
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    train = relationship("Train", back_populates="status_history")

class TrainPosition(Base):
    __tablename__ = "train_positions"

    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String(50), ForeignKey("trains.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id = Column(String(50), nullable=True, index=True)
    distance_along_track_km = Column(Float, default=0.0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    train = relationship("Train", back_populates="positions")
