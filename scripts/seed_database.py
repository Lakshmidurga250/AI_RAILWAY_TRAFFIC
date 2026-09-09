"""Database Seeder Script: Initializes default admin, stations, tracks, and trains."""
import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.database import engine, Base, SessionLocal
from backend.models.user import User
from backend.models.network import Station, Platform, Track, Junction, Signal
from backend.models.train import Train, ScheduleStop
from backend.app.security import get_password_hash
from simulation.network.loader import create_corridor_network
from datetime import datetime, timedelta, timezone

def seed():
    print("[INFO] Creating database schema tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Admin User
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@railway-ai.internal",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Lead Operations Dispatcher",
                role="admin",
                is_active=True
            )
            db.add(admin)
            print("[OK] Created default administrator: admin / AdminPass123!")

        # 2. Sync network stations
        net = create_corridor_network()
        for st in net.stations.values():
            existing_st = db.query(Station).filter(Station.id == st.id).first()
            if not existing_st:
                db_st = Station(
                    id=st.id,
                    name=st.name,
                    code=st.code,
                    latitude=st.latitude,
                    longitude=st.longitude,
                    zone=st.zone,
                    passenger_capacity=st.passenger_capacity,
                    current_occupancy=st.current_occupancy,
                    status=st.status
                )
                db.add(db_st)
                for p in st.platforms.values():
                    db_p = Platform(
                        id=p.id,
                        station_id=st.id,
                        platform_number=p.platform_number,
                        length=p.length_m,
                        capacity=p.capacity,
                        is_occupied=p.is_occupied,
                        status=p.status,
                        has_overhead_catenary=p.has_overhead_catenary
                    )
                    db.add(db_p)

        # 3. Sync tracks
        for trk in net.tracks.values():
            existing_trk = db.query(Track).filter(Track.id == trk.id).first()
            if not existing_trk:
                db_trk = Track(
                    id=trk.id,
                    name=trk.name,
                    source_node=trk.source_node,
                    target_node=trk.target_node,
                    length=trk.length_km,
                    max_speed=trk.max_speed_kmh,
                    gradient=trk.gradient_percent,
                    electrified=trk.electrified,
                    track_type=trk.track_type,
                    is_bidirectional=trk.is_bidirectional,
                    status=trk.status.value if hasattr(trk.status, "value") else trk.status
                )
                db.add(db_trk)

        db.commit()
        print("[OK] Railway infrastructure entities seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
