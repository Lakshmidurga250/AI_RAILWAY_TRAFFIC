"""National Railway Timetable and Fleet Scheduling Engine.

Generates realistic timetables, train schedules, dwell times, and speed trajectories
for Vande Bharat, Rajdhani, Shatabdi, Superfast Express, and Freight rakes across
all major high-density corridors.
"""
from typing import List, Dict, Any
import random
import time
from dataclasses import dataclass

@dataclass
class ScheduledStop:
    station_code: str
    station_name: str
    arrival_time_min: int   # minutes from start of service
    departure_time_min: int
    dwell_minutes: int
    platform: int
    distance_km: float

@dataclass
class NationalTrainSchedule:
    train_number: str
    name: str
    service_type: str  # VANDE_BHARAT, RAJDHANI, SHATABDI, SUPERFAST, FREIGHT_CONTAINER
    origin_code: str
    destination_code: str
    departure_time_hhmm: str
    arrival_time_hhmm: str
    max_speed_kmh: float
    rake_composition: str
    priority_level: int
    total_distance_km: float
    stops: List[ScheduledStop]

TRAIN_TEMPLATES = [
    ("22436", "Vande Bharat Express (NDLS-BSB)", "VANDE_BHARAT", "NDLS", "DDU", 160.0, 1),
    ("20901", "Vande Bharat Express (MMCT-GNC)", "VANDE_BHARAT", "MMCT", "ADI", 160.0, 1),
    ("20607", "Vande Bharat Express (MAS-MYS)", "VANDE_BHARAT", "MAS", "SBC", 160.0, 1),
    ("20701", "Vande Bharat Express (SC-Tpty)", "VANDE_BHARAT", "SC", "BZA", 160.0, 1),
    ("12952", "Mumbai Rajdhani Express", "RAJDHANI", "NDLS", "MMCT", 130.0, 2),
    ("12302", "Howrah Rajdhani Express", "RAJDHANI", "NDLS", "HWH", 130.0, 2),
    ("12434", "Chennai Rajdhani Express", "RAJDHANI", "NDLS", "MAS", 130.0, 2),
    ("12438", "Secunderabad Rajdhani Express", "RAJDHANI", "NDLS", "SC", 130.0, 2),
    ("12002", "Bhopal Shatabdi Express", "SHATABDI", "NDLS", "RKMP", 150.0, 2),
    ("12004", "Lucknow Shatabdi Express", "SHATABDI", "NDLS", "CNB", 130.0, 2),
    ("12028", "Bengaluru Shatabdi Express", "SHATABDI", "MAS", "SBC", 130.0, 2),
    ("12626", "Kerala Superfast Express", "SUPERFAST", "NDLS", "MAS", 110.0, 3),
    ("12724", "Telangana Superfast Express", "SUPERFAST", "NDLS", "SC", 120.0, 3),
    ("12840", "Howrah Mail", "SUPERFAST", "MAS", "HWH", 110.0, 3),
    ("12138", "Punjab Mail", "SUPERFAST", "NDLS", "CSMT", 110.0, 3),
    ("BOXN-901", "Heavy Haul Coal Rake", "FREIGHT_BULK", "DDU", "CNB", 75.0, 5),
    ("CONCOR-402", "Double Stack Container Express", "FREIGHT_CONTAINER", "ADI", "NDLS", 100.0, 4),
    ("BCN-304", "Foodgrain Special Freight", "FREIGHT_BULK", "BPL", "MAS", 75.0, 5),
    ("AUTO-501", "Automobile Transport Carrier", "FREIGHT_CONTAINER", "MAS", "NDLS", 90.0, 4),
]

def generate_corridor_timetables(multiplier: int = 15) -> List[NationalTrainSchedule]:
    """Generates an extensive multi-train timetable portfolio for corridor simulation."""
    schedules: List[NationalTrainSchedule] = []
    
    for idx, (base_num, name, stype, orig, dest, max_spd, priority) in enumerate(TRAIN_TEMPLATES):
        for run in range(multiplier):
            train_no = f"{base_num}-{run+1:02d}" if run > 0 else base_num
            dept_hour = (6 + (run * 2) + (idx % 3)) % 24
            dept_min = (run * 15 + idx * 7) % 60
            dept_str = f"{dept_hour:02d}:{dept_min:02d}"
            
            # Generate intermediary corridor stops
            dist = 400.0 + (idx * 50.0) + (run * 20.0)
            stops = [
                ScheduledStop(orig, orig, 0, 0, 0, random.randint(1, 6), 0.0),
                ScheduledStop("WAYPOINT-1", "Intermediate Junction A", 120, 125, 5, random.randint(1, 4), dist * 0.35),
                ScheduledStop("WAYPOINT-2", "Intermediate Junction B", 240, 245, 5, random.randint(1, 4), dist * 0.70),
                ScheduledStop(dest, dest, 360, 360, 0, random.randint(1, 8), dist)
            ]
            
            arr_hour = (dept_hour + 6) % 24
            arr_str = f"{arr_hour:02d}:{dept_min:02d}"

            schedule = NationalTrainSchedule(
                train_number=train_no,
                name=f"{name} (Run #{run+1})",
                service_type=stype,
                origin_code=orig,
                destination_code=dest,
                departure_time_hhmm=dept_str,
                arrival_time_hhmm=arr_str,
                max_speed_kmh=max_spd,
                rake_composition="22 Coaches (LHB / Vande 16-car rake)" if "FREIGHT" not in stype else "58 Wagons (BOXNHL/BLCA)",
                priority_level=priority,
                total_distance_km=round(dist, 1),
                stops=stops
            )
            schedules.append(schedule)

    return schedules

# Precomputed global schedule matrix
NATIONAL_SCHEDULES = generate_corridor_timetables(multiplier=20)

def get_timetable_matrix() -> Dict[str, Any]:
    return {
        "total_scheduled_trains": len(NATIONAL_SCHEDULES),
        "total_passenger_services": sum(1 for s in NATIONAL_SCHEDULES if "FREIGHT" not in s.service_type),
        "total_freight_rakes": sum(1 for s in NATIONAL_SCHEDULES if "FREIGHT" in s.service_type),
        "schedules": [
            {
                "train_number": s.train_number,
                "name": s.name,
                "type": s.service_type,
                "origin": s.origin_code,
                "destination": s.destination_code,
                "departure": s.departure_time_hhmm,
                "arrival": s.arrival_time_hhmm,
                "speed_kmh": s.max_speed_kmh,
                "priority": s.priority_level,
                "distance_km": s.total_distance_km,
                "stops_count": len(s.stops)
            }
            for s in NATIONAL_SCHEDULES
        ]
    }
