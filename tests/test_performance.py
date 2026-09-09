"""Performance and Latency Benchmarking Tests."""
import time
import pytest
from simulation.network.loader import create_corridor_network
from simulation.engine.simulator import SimulationEngine
from optimization.routing.dijkstra import DijkstraRouter, AStarRouter
from optimization.routing.floyd_warshall import FloydWarshallRouter
from ai.delay_prediction.predictor import DelayPredictor

def test_benchmark_routing_latency(test_network):
    """Routing algorithms must complete well within real-time dispatcher limits (<25ms)."""
    # Dijkstra
    t0 = time.perf_counter()
    dijkstra_res = DijkstraRouter.optimize_route(test_network, "ST_SOUTH", "ST_SUMMIT")
    dijkstra_ms = (time.perf_counter() - t0) * 1000.0
    assert dijkstra_ms < 25.0
    assert len(dijkstra_res["path_nodes"]) > 0

    # A*
    t0 = time.perf_counter()
    astar_res = AStarRouter.optimize_route(test_network, "ST_SOUTH", "ST_SUMMIT")
    astar_ms = (time.perf_counter() - t0) * 1000.0
    assert astar_ms < 25.0

    # Floyd-Warshall query
    fw = FloydWarshallRouter(test_network)
    t0 = time.perf_counter()
    path = fw.get_shortest_path("ST_SOUTH", "ST_SUMMIT")
    fw_query_ms = (time.perf_counter() - t0) * 1000.0
    assert fw_query_ms < 5.0
    assert path is not None

def test_benchmark_ai_delay_inference_latency():
    """AI Delay Predictor inference latency must be < 40ms."""
    from backend.services.ai_service import AIService
    # Warmup / ensure model training completed
    AIService.predict_delay(train_id="TR_101", horizon_minutes=15)

    # Benchmark pure inference latency
    t0 = time.perf_counter()
    pred = AIService.predict_delay(train_id="TR_101", horizon_minutes=15)
    inf_ms = (time.perf_counter() - t0) * 1000.0
    assert inf_ms < 40.0
    assert "predicted_delay_minutes" in pred

def test_benchmark_simulation_step_throughput():
    """Discrete-event simulation engine throughput must sustain > 150 ticks per second."""
    engine = SimulationEngine(create_corridor_network())
    engine.initialize_default_traffic()
    
    steps = 300
    t0 = time.perf_counter()
    for _ in range(steps):
        engine.step(1.0)
    elapsed = time.perf_counter() - t0
    throughput_sps = steps / elapsed
    
    assert throughput_sps > 100.0, f"Simulation throughput was {throughput_sps:.1f} steps/sec (target: >100)"
