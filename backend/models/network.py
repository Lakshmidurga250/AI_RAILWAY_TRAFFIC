"""Railway Network Models: Stations, Platforms, Tracks, Junctions, Signals, Switches, Weather, Maintenance."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from backend.app.database import Base

class Station(Base):
    __tablename__ = "stations"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String(50), default="Central")
    passenger_capacity = Column(Integer, default=5000)
    current_occupancy = Column(Integer, default=0)
    status = Column(String(30), default="OPERATIONAL")  # OPERATIONAL, CONGESTED, RESTRICTED, CLOSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    platforms = relationship("Platform", back_populates="station", cascade="all, delete-orphan")

class Platform(Base):
    __tablename__ = "platforms"
    
    id = Column(String(50), primary_key=True, index=True)
    station_id = Column(String(50), ForeignKey("stations.id"), nullable=False, index=True)
    platform_number = Column(String(10), nullable=False)
    length = Column(Float, default=400.0)  # meters
    capacity = Column(Integer, default=1)  # number of trains simultaneously (usually 1)
    is_occupied = Column(Boolean, default=False)
    current_train_id = Column(String(50), nullable=True)
    status = Column(String(30), default="AVAILABLE")  # AVAILABLE, OCCUPIED, MAINTENANCE, CLOSED
    has_overhead_catenary = Column(Boolean, default=True)
    
    station = relationship("Station", back_populates="platforms")

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_node = Column(String(50), nullable=False, index=True)
    target_node = Column(String(50), nullable=False, index=True)
    length = Column(Float, nullable=False)  # kilometers
    max_speed = Column(Float, default=160.0)  # km/h
    gradient = Column(Float, default=0.0)  # percentage incline/decline
    electrified = Column(Boolean, default=True)
    track_type = Column(String(30), default="MAINLINE")  # MAINLINE, SIDING, PASSING_LOOP, HIGH_SPEED, DEPOT
    is_bidirectional = Column(Boolean, default=False)
    status = Column(String(30), default="CLEAR")  # CLEAR, OCCUPIED, MAINTENANCE, BLOCKED, RESTRICTED
    current_train_id = Column(String(50), nullable=True)
    maintenance_reason = Column(String(255), nullable=True)
    speed_restriction = Column(Float, nullable=True)  # km/h if temporary restriction

class Junction(Base):
    __tablename__ = "junctions"
    
    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    max_throughput = Column(Integer, default=24)  # trains per hour
    current_load = Column(Integer, default=0)
    status = Column(String(30), default="CLEAR")  # CLEAR, CAUTION, CONGESTED, BLOCKED

class Switch(Base):
    __tablename__ = "switches"
    
    id = Column(String(50), primary_key=True, index=True)
    junction_id = Column(String(50), ForeignKey("junctions.id"), nullable=False)
    state = Column(String(20), default="NORMAL")  # NORMAL, REVERSE, LOCKED
    is_locked = Column(Boolean, default=False)
    locked_for_train_id = Column(String(50), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(String(50), primary_key=True, index=True)
    track_id = Column(String(50), nullable=False, index=True)
    location_km = Column(Float, default=0.0)
    aspect = Column(String(20), default="GREEN")  # GREEN, DOUBLE_YELLOW, YELLOW, RED
    signal_type = Column(String(30), default="AUTOMATIC")  # AUTOMATIC, CONTROLLED, DISTANT, SHUNT
    interlocked_with = Column(String(50), nullable=True)
    is_faulty = Column(Boolean, default=False)
    last_changed = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Maintenance(Base):
    __tablename__ = "maintenance"
    
    id = Column(String(50), primary_key=True, index=True)
    resource_type = Column(String(30), nullable=False)  # TRACK, SWITCH, SIGNAL, PLATFORM
    resource_id = Column(String(50), nullable=False, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String(30), default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    description = Column(Text, nullable=True)
    speed_limit_override = Column(Float, nullable=True)

class WeatherCondition(Base):
    __tablename__ = "weather_conditions"
    
    id = Column(Integer, primary_key=True, index=True)
    zone = Column(String(50), nullable=False, index=True)
    condition = Column(String(50), default="CLEAR")  # CLEAR, RAIN, HEAVY_RAIN, SNOW, FOG, HIGH_WINDS
    temperature_c = Column(Float, default=20.0)
    wind_speed_kmh = Column(Float, default=10.0)
    visibility_m = Column(Float, default=10000.0)
    friction_coefficient = Column(Float, default=1.0)  # 1.0 = optimal rail adhesion
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
