"""Tests for Disruptions, Delay Events, Schedules, and Timetable Revisions."""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database import SessionLocal, engine, Base
from backend.models.conflict import Disruption, DelayEvent
from backend.models.train import Schedule, ScheduleVersion
from backend.repositories.disruption_repository import DisruptionRepository, DelayEventRepository
from backend.repositories.schedule_repository import ScheduleRepository, ScheduleVersionRepository
from backend.services.disruption_service import DisruptionService
from simulation.engine.simulator import sim_engine

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

def test_schedule_version_and_schedule_repository(db):
    """Test ScheduleVersion and Schedule repositories."""
    v_repo = ScheduleVersionRepository(db)
    s_repo = ScheduleRepository(db)

    version_code = f"TIMETABLE_V_{int(datetime.now().timestamp())}"
    v = v_repo.create_version(version_code, "Master Corridor Timetable 2026", "Summer peak service revision")
    assert v.id is not None
    assert v.version_code == version_code

    active_v = v_repo.get_active_version()
    assert active_v is not None

    # Schedule association
    now = datetime.now(timezone.utc)
    train_id = f"TR_SCHED_{int(datetime.now().timestamp())}"
    sched = Schedule(
        id=f"SCH_{train_id}",
        train_id=train_id,
        version_id=v.id,
        valid_from=now,
        valid_to=now + timedelta(days=30),
        is_active=True
    )
    s_repo.create(sched)

    found = s_repo.get_active_schedule_for_train(train_id)
    assert found is not None
    assert found.version_id == v.id

def test_disruption_service_lifecycle_and_impact(db):
    """Test full disruption injection, impact calculation, simulation block, and resolution."""
    dis_id = f"DIS_{int(datetime.now().timestamp())}"
    # Inject disruption on an active track
    target_track = "TRK_01" if "TRK_01" in sim_engine.network.tracks else list(sim_engine.network.tracks.keys())[0]

    dis = DisruptionService.register_disruption(
        disruption_id=dis_id,
        disruption_type="TRACK_CLOSURE",
        affected_resource_type="TRACK",
        affected_resource_id=target_track,
        severity="CRITICAL",
        description="Broken rail detected by track circuit",
        duration_minutes=45,
        db=db
    )
    assert dis.id == dis_id
    assert dis.status == "ACTIVE"
    assert "projected_delay_minutes" in dis.impact_summary

    # Ensure track is marked BLOCKED in simulation
    assert sim_engine.network.tracks[target_track].status == "BLOCKED"

    # Verify active disruptions query
    actives = DisruptionService.list_disruptions(active_only=True, db=db)
    assert any(d.id == dis_id for d in actives)

    # Resolve disruption
    resolved = DisruptionService.resolve_disruption(dis_id, db=db)
    assert resolved.status == "RESOLVED"
    assert resolved.actual_end_time is not None

    # Ensure track is restored to CLEAR in simulation
    assert sim_engine.network.tracks[target_track].status == "CLEAR"

def test_delay_event_logging(db):
    """Test structured logging of primary and cascading delay incidents."""
    train_id = "TR_101"
    event = DisruptionService.log_delay_event(
        train_id=train_id,
        delay_minutes=12.5,
        delay_type="REACTIONARY",
        cause="Delayed departure due to late incoming crew connection",
        station_id="ST_CENTRAL",
        db=db
    )
    assert event.id is not None
    assert event.delay_minutes == 12.5
    assert event.delay_type == "REACTIONARY"

    # Retrieve delays for train
    history = DisruptionService.list_delays(train_id=train_id, db=db)
    assert len(history) >= 1
    assert any(e.id == event.id for e in history)

def test_disruptions_and_delays_api(client):
    """Test API endpoints for disruptions and delay events."""
    # 1. Post disruption
    dis_id = f"API_DIS_{int(datetime.now().timestamp())}"
    payload = {
        "id": dis_id,
        "disruption_type": "SIGNAL_FAILURE",
        "affected_resource_type": "TRACK",
        "affected_resource_id": "TRK_02",
        "severity": "HIGH",
        "description": "Aspect lamp burn out",
        "duration_minutes": 30
    }
    create_res = client.post("/conflicts/disruptions", json=payload)
    assert create_res.status_code == 201
    assert create_res.json()["id"] == dis_id

    # 2. List disruptions
    list_res = client.get("/conflicts/disruptions")
    assert list_res.status_code == 200
    assert any(d["id"] == dis_id for d in list_res.json())

    # 3. Resolve disruption
    resolve_res = client.post(f"/conflicts/disruptions/{dis_id}/resolve")
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # 4. Post and list delay event
    delay_payload = {
        "train_id": "TR_102",
        "delay_minutes": 8.0,
        "delay_type": "PRIMARY",
        "cause": "Waiting for single line token"
    }
    d_post_res = client.post("/conflicts/delays", json=delay_payload)
    assert d_post_res.status_code == 201

    d_list_res = client.get("/conflicts/delays?train_id=TR_102")
    assert d_list_res.status_code == 200
    assert len(d_list_res.json()) >= 1
