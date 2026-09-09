"""Pytest Global Test Fixtures."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from simulation.network.loader import create_corridor_network
from simulation.engine.simulator import SimulationEngine

@pytest.fixture(scope="session")
def test_network():
    """Provides an isolated corridor network for testing."""
    return create_corridor_network()

@pytest.fixture(scope="session")
def test_engine():
    """Provides an isolated simulation engine."""
    engine = SimulationEngine(create_corridor_network())
    engine.initialize_default_traffic()
    return engine

@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
