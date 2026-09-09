# Platform Architecture & Subsystem Specification

## 1. Monorepo Structure

```
railway-ai-optimization/
├── backend/
│   ├── app/               # Configuration, database engine, security & dependencies
│   ├── models/            # SQLAlchemy 2.0 ORM domain entities
│   ├── schemas/           # Pydantic validation and serialization schemas
│   ├── api/               # FastAPI modular endpoint routers (12 routers)
│   ├── services/          # Business logic, telemetry compilation, dispatch arbiter
│   ├── static/            # High-performance glassmorphic Control Center UI
│   └── main.py            # Application lifespan and ASGI entrypoint
│
├── simulation/
│   ├── network/           # Graph topology (NetworkX), elements, and corridor loader
│   ├── trains/            # SimulationTrain entity, kinematics, and Davis resistance
│   ├── signals/           # 4-aspect block signaling and headway spacing
│   ├── junctions/         # Point switch management and locking
│   ├── platforms/         # Platform allocation and dwell time calculation
│   ├── events/            # 16+ structured domain event definitions and EventBus
│   ├── conflicts/         # Spatial-temporal conflict detection engine
│   ├── scenarios/         # Disruption injection and what-if comparison
│   └── engine/            # SimulationEngine loop and DigitalTwin state shadow
│
├── ai/
│   ├── data/              # Ingestion service, synthetic data generator, data quality
│   ├── features/          # Feature engineering pipeline for trains and tracks
│   ├── delay_prediction/  # Multi-horizon delay prediction models (5m-60m)
│   ├── congestion_prediction/ # Network resource bottleneck forecasting
│   ├── demand_prediction/ # 24-hour station passenger flow and surge detection
│   ├── reinforcement_learning/ # Gymnasium environment, DQN agent, and policy trainer
│   ├── energy/            # Eco-driving traction and regenerative braking models
│   ├── explainability/    # Feature attribution (SHAP-proxy) and counterfactuals
│   └── registry/          # AI model registry, lifecycle and version tracking
│
├── optimization/
│   ├── routing/           # Dijkstra, A*, and Multi-Objective Pareto routers
│   ├── scheduling/        # Priority-constrained headway timetable optimizer
│   ├── platforms/         # Station platform allocation engine
│   ├── rescheduling/      # Real-time dynamic disruption recovery
│   └── conflicts/         # Autonomous conflict resolution arbiter
│
├── frontend/              # Standalone React 18, Vite, TypeScript & Tailwind CSS source
├── tests/                 # Complete Pytest test suite (30 automated tests)
├── monitoring/            # Prometheus metrics scraper and Grafana dashboards
├── docker/                # Multi-stage Dockerfiles for backend, worker, and frontend
└── scripts/               # Seeding, training, and simulation CLI utilities
```

## 2. Event-Sourcing Digital Twin Data Flow

```
[INFRASTRUCTURE & TRACKS]
          │
          ▼
[TRAIN KINEMATICS STEP] ───► [EVENT BUS] ───► [DIGITAL TWIN SNAPSHOT]
          │                       │                     │
          ▼                       │                     ▼
[CONFLICT DETECTOR] ◄─────────────┘           [FASTAPI WEBSOCKET (/ws/live)]
          │                                             │
          ▼                                             ▼
[OPTIMIZATION & DISPATCH ARBITER]              [OPERATIONS CONTROL CENTER]
```

## 3. Security & Access Control
* **JSON Web Tokens (JWT)**: HMAC-SHA256 signature with configurable expiration window.
* **Role-Based Access Control (RBAC)**: Supports `admin`, `dispatcher`, `operator`, and `viewer`.
* **Audit Logging**: Immutable logging of all dispatch commands, track status changes, and platform reassignments.
