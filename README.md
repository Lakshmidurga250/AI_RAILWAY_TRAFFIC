# AI Railway Traffic Optimization & Intelligent Train Management System

[![CI Test & Quality Suite](https://github.com/railway-ai/railway-optimization/actions/workflows/ci.yml/badge.svg)](https://github.com/railway-ai/railway-optimization/actions)
[![Docker Validation](https://github.com/railway-ai/railway-optimization/actions/workflows/docker.yml/badge.svg)](https://github.com/railway-ai/railway-optimization/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

A production-grade, discrete-event railway simulation, multi-horizon AI prediction, and multi-objective traffic optimization platform designed for modern operations control centers (OCC).

---

## 1. System Architecture

```
                               OPERATIONS CONTROL CENTER (WEB UI)
                        [Leaflet Real-time Map | SVG Track Schematics | Recharts]
                                                 ▲
                                                 │ WebSocket (/ws/live) & REST
                                                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI BACKEND APPLICATION CORE                              │
│                                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────────────────────┐ │
│  │   Auth & RBAC (JWT)   │  │ Train Fleet & Telemetry│  │ Network Infrastructure & Blocks │ │
│  └───────────────────────┘  └───────────────────────┘  └──────────────────────────────────┘ │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │                                 DIGITAL TWIN ENGINE                                    │ │
│  │         (Event-Sourcing • Synchronized Network Shadow • Telemetry Normalization)       │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
┌──────────────────────────────┐┌──────────────────────────────┐┌──────────────────────────────┐
│   DISCRETE-EVENT SIMULATOR   ││    AI PREDICTION PIPELINE    ││     OPTIMIZATION SUITE       │
│ • Kinematics (Davis Eq)      ││ • Multi-Horizon Delays       ││ • Multi-Objective Pareto     │
│ • 4-Aspect Signaling         ││   (5m, 10m, 15m, 30m, 60m)   ││ • Dijkstra & A* Pathfinding  │
│ • Point Switches & Interlock ││ • Congestion Classification  ││ • Conflict-Free Headway Sched│
│ • Platform Boarding/Dwell    ││ • Passenger Demand & Surges  ││ • Dynamic Disruption Resolver│
│ • Spatial Headway Conflict   ││ • Gymnasium RL Dispatch Env  ││ • Platform Assignment Engine │
│ • Disruption What-If Analyzer││ • Explainable AI (XAI / SHAP)││ • Eco-Driving Energy Profiles│
└──────────────────────────────┘└──────────────────────────────┘└──────────────────────────────┘
               │                               │                               │
               └───────────────────────────────┼───────────────────────────────┘
                                               ▼
                              PERSISTENCE & OBSERVABILITY LAYER
                    [SQLite / PostgreSQL TimescaleDB | Redis | Prometheus | Grafana]
```

---

## 2. Key Features

### 🚄 1. Railway Network Graph Engine
* Modeled as a directed MultiGraph using **NetworkX**.
* Represents 10+ stations, 20+ tracks (double track mainline, tunnels, bridges, sidings, high-speed bypasses), 4-aspect block signals, and motor-driven switches.
* Real-time GeoJSON spatial serialization.

### ⏱️ 2. High-Fidelity Discrete-Event Simulator
* Continuous-step train dynamics implementing the **Davis Equation** ($R = A + Bv + Cv^2$) for rolling and aerodynamic resistance.
* 4-aspect automatic block signaling (Green, Double Yellow, Yellow, Red) with headway enforcement.
* Real-time (1x), accelerated (5x-60x), step-by-step, and historical replay modes.

### ⚠️ 3. Real-Time Conflict Detection Arbiter
* Spatial-temporal headway violation detection (< 2.0 km spacing).
* Opposite-direction single track deadlock prevention.
* Junction convergence contention arbitration with priority preemption.
* Platform allocation overlap avoidance.

### 🧠 4. Explainable AI (XAI) Prediction Pipeline
* **Delay Prediction**: Multi-horizon regressors (5m, 10m, 15m, 30m, 60m) with feature attribution breakdown.
* **Congestion Forecaster**: Evaluates station, track, and junction bottleneck probability and duration.
* **Passenger Flow Forecaster**: 24-hour diurnal passenger demand curves with peak and surge anomaly detection.
* **Reinforcement Learning**: Gymnasium `RailwayGymEnv` supporting DQN and PPO policies with benchmark comparison against heuristic dispatchers.

### ⚡ 5. Multi-Objective Optimization Suite
* **Pareto Routing**: Simultaneous optimization of travel time, delay risk, track congestion, and traction energy.
* **Dynamic Rescheduling**: Rapid disruption mitigation for track closures, signal failures, and equipment breakdown with baseline vs optimized comparison.
* **Platform Optimizer**: Matching train lengths, passenger flow accessibility, and dwell clearance.
* **Energy Optimization**: Eco-driving speed profiles with coasting windows and regenerative braking recovery (up to 35% kinetic energy recovered).

### 🖥️ 6. Operations Control Center Dashboard
* Dark glassmorphic user interface served directly at `http://localhost:8000`.
* Interactive **Leaflet.js** map with live animated train telemetry markers.
* Instant simulation control bar, KPI widgets, and autonomous conflict resolution actions.
* Standalone React + Vite + Tailwind CSS source code in `frontend/`.

---

## 3. Quick Start (Local Run)

### Prerequisites
* Python 3.12+
* Git

### Installation & Run

```bash
# 1. Clone the repository
git clone https://github.com/railway-ai/railway-optimization.git
cd railway-optimization

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed initial database (creates default stations, tracks, and admin user)
python scripts/seed_database.py

# 4. Train AI models and neural policies
python scripts/train_ai_models.py

# 5. Launch FastAPI server & Control Center UI
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser:
* **Interactive Control Center UI**: `http://localhost:8000`
* **Swagger Interactive API Documentation**: `http://localhost:8000/docs`
* **ReDoc Documentation**: `http://localhost:8000/redoc`
* **Prometheus Metrics**: `http://localhost:8000/metrics`

Default Admin Credentials:
* **Username**: `admin`
* **Password**: `AdminPass123!`

---

## 4. Docker Deployment

Launch the full stack (Backend, Worker, React Frontend, PostgreSQL, Redis, Prometheus, Grafana) via Docker Compose:

```bash
docker compose up --build -d
```

Service URLs:
* **Frontend Web Dashboard**: `http://localhost:3000`
* **Backend API**: `http://localhost:8000`
* **Grafana Dashboards**: `http://localhost:3001` (admin / admin)
* **Prometheus**: `http://localhost:9090`

---

## 5. Running Automated Tests

The platform includes a test suite covering graph invariants, physics kinematics, conflict detection, AI inference, and FastAPI endpoints:

```bash
python -m pytest tests/ -v
```

---

## 6. Safety & Advisory Notice

> [!IMPORTANT]
> **SIMULATION & DECISION SUPPORT PLATFORM ONLY**
> 
> This software is an engineering simulation, machine learning research, and advisory decision-support platform. It is **NOT** a certified railway interlocking system (such as CENELEC EN 50126/EN 50128/EN 50129 or SIL-4). All automated recommendations and conflict resolution actions must be validated by licensed human train dispatchers prior to field execution.

---

## 7. License

MIT License. Designed and engineered for high-performance railway optimization research.
