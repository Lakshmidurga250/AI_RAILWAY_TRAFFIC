# Testing & Quality Assurance Guide

The project enforces strict quality standards through a comprehensive multi-tier test suite encompassing unit tests, integration tests, mathematical invariant property tests, performance latency benchmarks, and load testing.

---

## 1. Test Suite Architecture

The repository contains **18 automated test files** in `tests/`, covering all system layers:

| Test Suite | File | Tests | Focus Area |
|---|---|:---:|---|
| **API Endpoints** | `tests/test_api.py` | 12 | Health, trains, stations, graph, simulation, models, analytics, reports |
| **Network & Routing** | `tests/test_network.py` | 5 | MultiDiGraph topology, shortest path, $K$-alternatives, track closures, GeoJSON |
| **Simulation Engine** | `tests/test_simulation.py` | 3 | Kinematic physics, discrete step progression, event sourcing bus |
| **What-If & Replay** | `tests/test_what_if_replay.py` | 3 | Historical scrubbing buffer, delay injection, closure perturbation |
| **AI Delay Predictor** | `tests/test_ai_delay.py` | 2 | Multi-horizon training, feature pipeline, inference accuracy ($R^2 > 0.85$) |
| **AI Congestion** | `tests/test_ai_congestion.py` | 1 | Spatial bottleneck scoring, capacity utilization, mitigation advice |
| **AI Demand** | `tests/test_ai_demand.py` | 1 | Diurnal passenger forecast curve, peak hour detection |
| **AI Model Registry**| `tests/test_model_registry.py` | 3 | Training triggers, benchmark evaluation, version history & audit |
| **Conflict Arbiter** | `tests/test_conflicts.py` | 2 | Spatial headway violation, opposite-track deadlock prevention |
| **Optimization** | `tests/test_optimization.py` | 5 | Dijkstra vs. A*, Pareto routing, platform assignment, dynamic rescheduling, Floyd-Warshall |
| **Energy & Eco** | `tests/test_energy.py` | 1 | Coasting profile generation, regenerative braking, $\text{CO}_2$ abatement |
| **Explainable AI** | `tests/test_explainability.py` | 2 | SHAP-proxy feature attribution, counterfactual recommendation |
| **RL Dispatcher** | `tests/test_rl.py` | 3 | Gymnasium observation/action spaces, reward shaping, baseline comparison |
| **Scenarios & Baseline**| `tests/test_scenarios.py` | 3 | Standard presets, dynamic scenario injector, 3-tier comparative metrics |
| **Observability & Probes**| `tests/test_observability.py`| 5 | General health, `/health/live`, `/health/ready`, security headers, `/metrics` |
| **Data Quality** | `tests/test_ingestion.py` | 4 | CSV/JSON parsers, range checks, temporal monotonicity, missing values |
| **Mathematical Invariants**| `tests/test_properties.py` | 4 | Non-negative graph distances, monotonic Davis resistance, speed envelopes |
| **Performance Benchmarks**| `tests/test_performance.py`| 3 | Routing latency (<50ms), inference latency (<10ms), step throughput (>500 steps/s) |
| **Total Automated Tests**| — | **62** | **100% Passing (0 failures, 0 regressions)** |

---

## 2. Running Automated Tests

Run the full pytest suite locally:

```bash
# Run all 62 tests
python -m pytest -v

# Run with execution timing profile
python -m pytest --durations=10

# Run a specific subsystem
python -m pytest tests/test_optimization.py -v
```

---

## 3. Mathematical Invariant & Property-Based Testing (`test_properties.py`)

Using formal property checking and **Hypothesis**, critical physical and mathematical safety invariants are validated:
1. **Graph Distances**: Network distances along any directed track edge are strictly positive ($d > 0$).
2. **Davis Resistance Monotonicity**: Rolling aerodynamic resistance monotonically increases with velocity: $\forall v_1 < v_2 \implies R(v_1) < R(v_2)$.
3. **Kinematic Bounds**: Train speed never exceeds design maximum ($v_t \le v_{\max}$) and never drops below zero ($v_t \ge 0$).
4. **Safety Headway Spacing**: Scheduled stops at identical station platforms preserve minimum required headway spacing ($\Delta t \ge 180 \text{ s}$).

---

## 4. Performance & Latency Benchmarks (`test_performance.py`)

Production performance requirements are enforced via automated assertions:
- **Routing Engine Latency**: Shortest path computation across the corridor graph executes in **$< 50 \text{ ms}$**.
- **AI Inference Latency**: Multi-horizon delay prediction batch executes in **$< 10 \text{ ms}$**.
- **Simulation Throughput**: Discrete-event kinematic stepping achieves **$> 500 \text{ steps/second}$**, ensuring frictionless 60x acceleration.

---

## 5. Load & Stress Testing (`locustfile.py`)

A production **Locust** load testing suite is located in `tests/locustfile.py` to evaluate backend concurrency under simulated dispatcher load:

```bash
# Run headless Locust load test for 60 seconds with 50 concurrent dispatchers
locust -f tests/locustfile.py --headless -u 50 -r 5 --run-time 60s --host http://localhost:8000
```
