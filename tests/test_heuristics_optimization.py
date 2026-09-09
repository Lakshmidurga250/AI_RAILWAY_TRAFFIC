"""Tests for Genetic Algorithm, Particle Swarm, Simulated Annealing, and Run Audits."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database import SessionLocal, engine, Base
from backend.repositories.optimization_repository import OptimizationRepository
from backend.services.optimization_service import OptimizationService
from simulation.engine.simulator import sim_engine
from optimization.routing.genetic_algorithm import GeneticAlgorithmRouter
from optimization.routing.particle_swarm import ParticleSwarmRouter
from optimization.routing.simulated_annealing import SimulatedAnnealingRouter

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

def test_genetic_algorithm_router():
    """Test GeneticAlgorithmRouter solution generation and Pareto metrics."""
    res = GeneticAlgorithmRouter.optimize_route(
        network=sim_engine.network,
        origin_id="ST_SOUTH",
        destination_id="ST_NORTH",
        generations=10,
        population_size=8
    )
    assert "optimal_route" in res
    route = res["optimal_route"]
    assert len(route["station_ids"]) >= 2
    assert route["station_ids"][0] == "ST_SOUTH"
    assert route["station_ids"][-1] == "ST_NORTH"
    assert route["total_distance_km"] > 0
    assert route["composite_score"] > 0
    assert res["algorithm"] == "GENETIC_ALGORITHM"

def test_particle_swarm_router():
    """Test ParticleSwarmRouter swarm convergence."""
    res = ParticleSwarmRouter.optimize_route(
        network=sim_engine.network,
        origin_id="ST_SOUTH",
        destination_id="ST_NORTH",
        iterations=8,
        swarm_size=6
    )
    assert "optimal_route" in res
    route = res["optimal_route"]
    assert route["station_ids"][0] == "ST_SOUTH"
    assert route["station_ids"][-1] == "ST_NORTH"
    assert route["total_distance_km"] > 0
    assert res["algorithm"] == "PARTICLE_SWARM"

def test_simulated_annealing_router():
    """Test SimulatedAnnealingRouter stochastic search."""
    res = SimulatedAnnealingRouter.optimize_route(
        network=sim_engine.network,
        origin_id="ST_SOUTH",
        destination_id="ST_NORTH",
        initial_temp=50.0,
        cooling_rate=0.85,
        max_iterations=15
    )
    assert "optimal_route" in res
    route = res["optimal_route"]
    assert route["station_ids"][0] == "ST_SOUTH"
    assert route["station_ids"][-1] == "ST_NORTH"
    assert route["total_distance_km"] > 0
    assert res["algorithm"] == "SIMULATED_ANNEALING"
    assert res["final_temperature"] < 50.0

def test_optimization_repository_audit(db):
    """Test recording and querying optimization runs."""
    import uuid
    test_run_id = f"OPT_TEST_AUDIT_{uuid.uuid4().hex[:8]}"
    repo = OptimizationRepository(db)
    run = repo.record_run(
        run_id=test_run_id,
        optimization_type="ROUTING",
        algorithm="GENETIC_ALGORITHM",
        execution_time_ms=12.4,
        baseline_delay_minutes=25.0,
        optimized_delay_minutes=8.0,
        delay_reduction_percentage=68.0,
        baseline_energy_kwh=150.0,
        optimized_energy_kwh=120.0,
        energy_savings_percentage=20.0,
        conflicts_resolved=1,
        explanation="Genetic algorithm avoided bottleneck track segment"
    )
    assert run.id == test_run_id
    assert run.delay_reduction_percentage == 68.0

    recent = repo.get_recent_runs(limit=10, optimization_type="ROUTING")
    assert any(r.id == test_run_id for r in recent)

def test_optimization_api_metaheuristics(client):
    """Test API endpoints for GA, PSO, SA and historical runs."""
    # 1. GA via API
    ga_payload = {
        "train_id": "TR_TEST_GA",
        "origin_station_id": "ST_SOUTH",
        "destination_station_id": "ST_NORTH",
        "algorithm": "GENETIC_ALGORITHM"
    }
    ga_res = client.post("/optimization/route", json=ga_payload)
    assert ga_res.status_code == 200
    assert ga_res.json()["algorithm"] == "GENETIC_ALGORITHM"

    # 2. PSO via API
    pso_payload = {
        "train_id": "TR_TEST_PSO",
        "origin_station_id": "ST_SOUTH",
        "destination_station_id": "ST_NORTH",
        "algorithm": "PARTICLE_SWARM"
    }
    pso_res = client.post("/optimization/route", json=pso_payload)
    assert pso_res.status_code == 200
    assert pso_res.json()["algorithm"] == "PARTICLE_SWARM"

    # 3. SA via API
    sa_payload = {
        "train_id": "TR_TEST_SA",
        "origin_station_id": "ST_SOUTH",
        "destination_station_id": "ST_NORTH",
        "algorithm": "SIMULATED_ANNEALING"
    }
    sa_res = client.post("/optimization/route", json=sa_payload)
    assert sa_res.status_code == 200
    assert sa_res.json()["algorithm"] == "SIMULATED_ANNEALING"

    # 4. List optimization runs
    runs_res = client.get("/optimization/runs?limit=20")
    assert runs_res.status_code == 200
    assert isinstance(runs_res.json(), list)
    assert len(runs_res.json()) >= 1
