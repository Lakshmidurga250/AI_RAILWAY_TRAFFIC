"""Database Seeder Script: Populates initial stations, tracks, trains, and admin account."""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.database import engine, Base, SessionLocal
from backend.models.user import User
from backend.models.network import Station, Platform, Track
from backend.app.security import get_password_hash
from simulation.network.loader import create_corridor_network

def seed():
    print("[*] Creating database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed RBAC Roles and Permissions
        from backend.repositories.role_repository import RoleRepository
        from backend.repositories.user_repository import UserRepository
        from backend.repositories.train_repository import TrainRepository
        role_repo = RoleRepository(db)
        user_repo = UserRepository(db)
        train_repo = TrainRepository(db)
        role_repo.seed_defaults()
        train_repo.seed_types_and_categories()
        print("[+] Seeded default RBAC roles (admin, dispatcher, operator, viewer), permissions matrix, and train types.")

        # 2. Admin User
        admin = user_repo.get_by_username("admin")
        if not admin:
            admin = User(
                username="admin",
                email="admin@railway-ai.internal",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Operations Commander",
                role="admin"
            )
            admin = user_repo.create(admin)
            admin_role = role_repo.get_by_name("admin")
            if admin_role:
                user_repo.assign_role_to_user(admin.id, admin_role.id)
            print("[+] Seeded admin user: 'admin' (password: 'AdminPass123!') with admin role")
        else:
            admin_role = role_repo.get_by_name("admin")
            if admin_role:
                user_repo.assign_role_to_user(admin.id, admin_role.id)

        # 2. Network Stations & Tracks from corridor network
        net = create_corridor_network()
        for st_id, st in net.stations.items():
            existing_st = db.query(Station).filter(Station.id == st_id).first()
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
                db.flush()

                for p_id, p in st.platforms.items():
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

        for trk_id, trk in net.tracks.items():
            existing_trk = db.query(Track).filter(Track.id == trk_id).first()
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
        print(f"[+] Successfully seeded {len(net.stations)} stations and {len(net.tracks)} tracks into database.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
