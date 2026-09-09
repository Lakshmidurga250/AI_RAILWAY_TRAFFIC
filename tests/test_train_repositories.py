"""Tests for Train and Network Domain Repositories, History, and Telemetry."""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database import SessionLocal, engine, Base
from backend.models.train import Train, TrainType, TrainCategory, TrainStatusHistory, TrainPosition
from backend.models.network import Station, Platform, Track
from backend.repositories.train_repository import TrainRepository
from backend.repositories.network_repository import StationRepository, PlatformRepository, TrackRepository
from backend.services.train_service import TrainService
from backend.schemas.train import TrainCreate, TrainUpdate

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_train_repository_crud_and_search(db):
    """Test TrainRepository persistence, status transition, and search filtering."""
    repo = TrainRepository(db)
    repo.seed_types_and_categories()

    train_id = f"TR_UNIT_{int(datetime.now().timestamp())}"
    now = datetime.now(timezone.utc)
    t = Train(
        id=train_id,
        train_number=f"EXP-{train_id[-4:]}",
        name="Express Pioneer",
        train_type="HIGH_SPEED",
        origin_station_id="ST_CENTRAL",
        destination_station_id="ST_NORTH",
        priority=8,
        status="SCHEDULED",
        scheduled_departure=now,
        scheduled_arrival=now + timedelta(hours=2)
    )
    created = repo.create(t)
    assert created.id == train_id

    # Record status transition
    st_hist = repo.record_status_transition(train_id, "RUNNING", reason="Departed on green aspect")
    assert st_hist is not None
    assert st_hist.new_status == "RUNNING"
    assert st_hist.previous_status == "SCHEDULED"

    # Search
    search_results = repo.search_trains(status="RUNNING", search_query="Pioneer")
    assert any(x.id == train_id for x in search_results)

    # Status history
    hist = repo.get_status_history(train_id)
    assert len(hist) >= 1
    assert hist[0].new_status == "RUNNING"

def test_train_position_recording(db):
    """Test recording and querying spatial position breadcrumbs."""
    repo = TrainRepository(db)
    train_id = f"TR_POS_{int(datetime.now().timestamp())}"
    now = datetime.now(timezone.utc)
    t = Train(
        id=train_id,
        train_number=f"POS-{train_id[-4:]}",
        name="Telemetry Scout",
        origin_station_id="ST_CENTRAL",
        destination_station_id="ST_NORTH",
        scheduled_departure=now,
        scheduled_arrival=now + timedelta(hours=1)
    )
    repo.create(t)

    # Record positions
    repo.record_position(train_id, "TRK_01", 5.2, 40.7128, -74.0060, 120.5)
    repo.record_position(train_id, "TRK_01", 8.4, 40.7180, -74.0010, 145.0)

    trail = repo.get_positions_trail(train_id)
    assert len(trail) >= 2
    assert trail[0].speed_kmh == 145.0

def test_network_repositories(db):
    """Test Station, Platform, and Track repositories."""
    st_repo = StationRepository(db)
    pl_repo = PlatformRepository(db)
    tr_repo = TrackRepository(db)

    # Station occupancy test
    st = st_repo.get_by(code="GUT")
    if not st:
        st = Station(id="ST_TEST_GUT", name="Test Terminal", code="TT1", latitude=40.0, longitude=-74.0, passenger_capacity=1000)
        st_repo.create(st)

    updated_st = st_repo.update_occupancy(st.id, int(st.passenger_capacity * 0.95))
    assert updated_st.status == "CONGESTED"

    # Platform assignment
    pl = pl_repo.get_by(station_id=st.id)
    if not pl:
        pl = Platform(id="PL_TEST_1", station_id=st.id, platform_number="1", status="AVAILABLE")
        pl_repo.create(pl)

    assigned = pl_repo.assign_train(pl.id, "TR_TEST_99")
    assert assigned is True
    assert pl_repo.get(pl.id).is_occupied is True

    released = pl_repo.release_platform(pl.id)
    assert released is True
    assert pl_repo.get(pl.id).is_occupied is False

    # Track status
    trk = tr_repo.list(limit=1)
    if trk:
        tr_repo.set_track_status(trk[0].id, "MAINTENANCE", reason="Rail grinding", speed_restriction=40.0)
        assert tr_repo.get(trk[0].id).status == "MAINTENANCE"
        assert tr_repo.get(trk[0].id).speed_restriction == 40.0
        # Reset back
        tr_repo.set_track_status(trk[0].id, "CLEAR")

def test_train_api_crud_and_emergency_stop(client):
    """Test full API workflow: create, get, update, emergency stop, history, and delete."""
    now_iso = datetime.now(timezone.utc).isoformat()
    future_iso = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
    test_id = f"TR_API_{int(datetime.now().timestamp())}"

    # 1. Create train
    payload = {
        "id": test_id,
        "train_number": f"NO-{test_id[-4:]}",
        "name": "Super Express",
        "train_type": "HIGH_SPEED",
        "origin_station_id": "ST_CENTRAL",
        "destination_station_id": "ST_NORTH",
        "priority": 7,
        "scheduled_departure": now_iso,
        "scheduled_arrival": future_iso
    }
    create_res = client.post("/trains", json=payload)
    assert create_res.status_code == 201
    assert create_res.json()["id"] == test_id

    # 2. Get train
    get_res = client.get(f"/trains/{test_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Super Express"

    # 3. Update priority & speed
    p_res = client.post(f"/trains/{test_id}/priority?priority=9")
    assert p_res.status_code == 200

    # 4. Emergency stop
    em_res = client.post(f"/trains/{test_id}/emergency-stop?reason=OBSTRUCTION_DETECTED")
    assert em_res.status_code == 200

    # 5. Verify history captured the transitions
    hist_res = client.get(f"/trains/{test_id}/history")
    assert hist_res.status_code == 200
    statuses = [h["new_status"] for h in hist_res.json()]
    assert "STOPPED" in statuses

    # 6. Delete train
    del_res = client.delete(f"/trains/{test_id}")
    assert del_res.status_code == 200
