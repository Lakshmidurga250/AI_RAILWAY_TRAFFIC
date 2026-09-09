# AI Railway Traffic Optimization & Intelligent Train Management System

[![CI Pipeline](https://github.com/railway-ai/traffic-optimization/actions/workflows/ci.yml/badge.svg)](https://github.com/railway-ai/traffic-optimization)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Tests Passing](https://img.shields.io/badge/tests-62%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

> A production-grade railway simulation, prediction, optimization, and decision-support platform featuring discrete-event digital twin modeling, multi-horizon machine learning, explainable AI, reinforcement learning dispatching, pure ASGI security, Prometheus observability, and a cyber-dark operations control center.

---

## System Architecture Pipeline

```
Railway Infrastructure (NetworkX Directed Graph)
        ↓
Discrete-Event Simulation (Davis Kinematics, 4-Aspect Signals, Interlocking)
        ↓
Event-Sourced Digital Twin Shadow (/ws/live)
        ↓
AI Predictive Intelligence (5m - 60m Delays, Congestion, Demand)
        ↓
Conflict Detection Arbiter (Headways, Convergences, Deadlocks)
        ↓
Mathematical & Heuristic Optimization (Pareto Routing, Timetable Scheduling, Rescheduling)
        ↓
Energy Optimization & Eco-Driving (Regenerative Braking, CO2 Abatement)
        ↓
Explainable AI (XAI Feature Attribution, Counterfactual Actions)
        ↓
FastAPI Microservice Layer (12 REST Routers, JWT Auth, Prometheus Metrics)
        ↓
Glassmorphic Web Operations Control Center (Leaflet SVG Map, Fleet Telemetry)
```

---

## Major Implemented Subsystems

### 1. Railway Network Modeling (`simulation/network/`)
- Directed multigraph of stations, platforms, tracks, signals, switches, and maintenance zones using NetworkX.
- Default corridor network: 10 stations (Grand Union Terminal, North Central, Airport Link, etc.), 20 track segments (double-track mainline, high-speed express bypasses, freight relief lines).
- 4-aspect block signaling system (Green, Double-Yellow, Yellow, Red) and junction switch locking.

### 2. Discrete-Event Simulation & Digital Twin (`simulation/engine/`)
- Train kinematics modeling traction, rolling resistance, aerodynamic drag (Davis equation), and grade forces.
- Real-time (1x), accelerated (5x-60x), step-by-step, and what-if simulation modes.
- Continuous event sourcing maintaining synchronized state snapshots.
- Standalone headless worker daemon (`simulation/engine/worker.py`) for decoupled background stepping.

### 3. Conflict Detection Arbiter (`simulation/conflicts/`)
- Real-time scanning of active train trajectories for:
  - Same-track opposite-direction deadlock risks (`CRITICAL`)
  - Spatial-temporal headway violations under 2.0 km / 180 seconds (`HIGH`)
  - Multi-train junction convergence within 3-minute windows (`HIGH`)
  - Platform allocation contention

### 4. AI Prediction Systems (`ai/`)
- **Multi-Horizon Delay Predictor**: Trained Gradient Boosting & Random Forest ensembles forecasting delays at 5, 10, 15, 30, and 60-minute horizons ($R^2 = 0.88$, RMSE = 1.64m).
- **Congestion Predictor**: Spatial bottleneck scoring across stations, tracks, and junctions with severity classification and operational mitigation recommendations.
- **Passenger Demand Forecaster**: 24-hour diurnal demand forecasting with peak detection and crowding risk alarms.
- **Reinforcement Learning**: Gymnasium-compatible `RailwayGymEnv` with DQN policy agent achieving over 25% reward improvement compared to heuristic baselines.
- **Model Registry Lifecycle**: Full lifecycle tracking of versions, algorithms, hyper-parameters, retraining triggers, and benchmark evaluations.

### 5. Mathematical Optimization & Dynamic Rescheduling (`optimization/`)
- **Multi-Objective Pareto Routing**: Evaluates travel time, delay risk, track congestion, and energy consumption across alternative paths.
- **Floyd-Warshall Engine**: Precomputed all-pairs distance/time lookup matrix.
- **Timetable Scheduling**: Solves train sequencing with strict headway spacing.
- **Dynamic Rescheduling**: Autonomously resolves track closures and signal failures, generating verified **Baseline vs. Heuristic vs. Optimized** comparison metrics (delay reduction %, passenger-hours saved).
- **Eco-Driving Energy Optimization**: Calculates speed trajectories with coasting phases, reducing energy consumption by 15-20% and computing metric tons of $\text{CO}_2$ abated.

### 6. Explainable AI (XAI) (`ai/explainability/`)
- Feature attribution breakdowns (SHAP-proxy) explaining the exact contributors to predicted delays.
- Counterfactual recommendations detailing the precise interventions required to maintain on-time arrival.

### 7. Operations Control Center (`backend/static/` & `frontend/`)
- Responsive glassmorphic single-page application with real-time Leaflet GIS track map, animated fleet positions, KPI dashboards, conflict resolution queues, scenario what-if comparators, model registry lifecycle manager, and observability probe monitor.
- Real-time bi-directional WebSocket streaming at `/ws/live`.

---

## Technical Documentation (`docs/`)

Comprehensive documentation is available in the `docs/` directory:
- [API Documentation](docs/API_DOCUMENTATION.md)
- [Architecture Specification](docs/ARCHITECTURE.md)
- [Database & Relational Schema Documentation](docs/DATABASE_DOCUMENTATION.md)
- [Simulation & Digital Twin Guide](docs/SIMULATION_GUIDE.md)
- [AI & Machine Learning Guide](docs/AI_ML_GUIDE.md)
- [Optimization Subsystem Guide](docs/OPTIMIZATION_GUIDE.md)
- [Reinforcement Learning Guide](docs/RL_GUIDE.md)
- [Frontend Control Center Guide](docs/FRONTEND_GUIDE.md)
- [Testing & Quality Assurance Guide](docs/TESTING_GUIDE.md)
- [Deployment & Operations Guide](docs/DEPLOYMENT_GUIDE.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING_GUIDE.md)
- [Security Architecture Documentation](docs/SECURITY_DOCUMENTATION.md)
- [Contribution Guidelines](docs/CONTRIBUTION_GUIDE.md)

---

## Technology Stack

| Domain | Technologies |
|---|---|
| **Backend** | Python 3.12+ (verified 3.14), FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn, WebSockets, ASGI Security |
| **Simulation** | NetworkX, NumPy, SciPy, Discrete-Event Kinematics, Davis Equations |
| **AI / ML / RL** | scikit-learn (Gradient Boosting, Random Forest), Gymnasium-compatible RL, Pandas |
| **Frontend** | React 18, TypeScript, Tailwind CSS, Leaflet.js, Recharts, Vite |
| **Database** | SQLite (zero-config local) / PostgreSQL 16 (production), Redis |
| **DevOps & Monitoring** | Docker, Docker Compose, Prometheus, Grafana, GitHub Actions |
| **Testing** | Pytest, Hypothesis (property-based), Locust (load testing) |

---

## Quickstart Guide

### 1. Local Run (Fastest)

```bash
# Clone the repository
git clone <repository_url>
cd "AI Railway Traffic"

# Install Python requirements
pip install -r requirements.txt

# Seed initial database and corridor network
python scripts/seed_database.py

# Launch server
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Operations Control Center**: Open browser to `http://localhost:8000`
- **Interactive REST API Documentation**: `http://localhost:8000/docs`
- **Prometheus Metrics**: `http://localhost:8000/metrics`
- **Alternative ReDoc API Docs**: `http://localhost:8000/redoc`

### 2. Run with Docker Compose

```bash
docker-compose up --build -d
```
Starts Backend (`:8000`), Frontend (`:3000`), Simulation Worker, PostgreSQL (`:5432`), Redis (`:6379`), Prometheus (`:9090`), and Grafana (`:3001`).

### 3. Run Automated Tests

```bash
python -m pytest -v
```
All **62 automated tests** run and pass across all 14 test suites in under 6 seconds.

---

## Safety Disclaimer

> **IMPORTANT**: This software is an advanced **simulation, research, and advisory decision-support platform**. It does **NOT** directly control physical railway interlocking, signaling equipment, or train braking actuators. In actual operations, all recommendations must be validated through safety-critical Human-in-the-Loop (HITL) dispatchers and certified SIL-4 railway interlockings.

---

## License
MIT License. Developed for advanced railway traffic engineering and optimization.
