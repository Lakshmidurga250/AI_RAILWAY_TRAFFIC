# Railway Traffic Optimization & Management System - REST API Reference

The backend exposes a comprehensive, asynchronous RESTful API built on **FastAPI** with **Pydantic v2** validation, OpenAPI 3.1 specifications, pure ASGI security middleware, and real-time WebSocket capabilities.

Interactive Swagger documentation is available at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## Base Configuration & Standards

- **Base URL**: `http://localhost:8000`
- **Default Content Type**: `application/json`
- **Authentication**: JWT Bearer token via `Authorization: Bearer <token>`
- **Security Headers**: Injected via pure ASGI middleware:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Referrer-Policy: strict-origin-when-cross-origin`

---

## 1. Authentication & RBAC (`/auth`)

| Method | Path | Description | Permissions / Roles |
|---|---|---|---|
| `POST` | `/auth/login` | Authenticates user; returns Access Token, Refresh Token, and Permissions | Public |
| `POST` | `/auth/refresh` | Rotates refresh token and issues new access token pair | Public / Client Session |
| `POST` | `/auth/logout` | Revokes active refresh token | Public / Client Session |
| `POST` | `/auth/register` | Registers a new user account with default role assignment | Public / Admin |
| `GET` | `/auth/me` | Fetches current user profile and effective permissions list | Authenticated |
| `GET` | `/auth/roles` | Lists system roles and assigned permission matrix | `admin`, `dispatcher` |
| `GET` | `/auth/permissions` | Lists all discrete system permissions | Authenticated |
| `POST` | `/auth/roles/assign` | Assigns a role to a user | `admin` |
| `GET` | `/auth/events` | Queries structured security and audit events with Request ID correlation | `admin` |

---

## 2. Train Fleet Management (`/trains`)

| Method | Path | Description | Permissions / Roles |
|---|---|---|---|
| `GET` | `/trains` | Retrieves all active and timetabled fleet trains, filterable by status | Public / Viewer |
| `POST` | `/trains` | Registers and timetables a new train in the database repository | `trains:write` |
| `GET` | `/trains/{id}` | Fetches full train state, kinematics, telemetry, and planned stops | Public / Viewer |
| `PUT` | `/trains/{id}` | Updates operational train parameters (priority, target speed, status) | `trains:write` |
| `DELETE` | `/trains/{id}` | Cancels and removes a train from the fleet | `trains:delete` |
| `POST` | `/trains/{id}/priority` | Commands priority level adjustments (1–10) | `trains:write` |
| `POST` | `/trains/{id}/speed` | Commands target speed adjustment (0–300 km/h) | `trains:write` |
| `POST` | `/trains/{id}/emergency-stop` | Executes immediate emergency brake, halts train, and logs transition | `trains:write` |
| `GET` | `/trains/{id}/history` | Retrieves chronological status transition history (`train_status_history`) | `trains:read` |
| `GET` | `/trains/{id}/positions` | Retrieves spatial position breadcrumbs (`train_positions`) for GIS maps | `trains:read` |

---

## 3. Station & Platform Infrastructure (`/stations`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/stations` | Lists all operational stations in the corridor |
| `GET` | `/stations/{id}` | Station details including passenger capacity |
| `GET` | `/stations/{id}/platforms`| Platform allocation, catenary status, and occupancy |

---

## 4. Railway Network & Interlocking (`/network`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/network/graph` | Directed multigraph topology (nodes, edges, lengths, speeds) |
| `GET` | `/network/tracks` | All track segments with status and speed limits |
| `PUT` | `/network/tracks/{id}/status`| Toggles maintenance closure or speed restriction |
| `GET` | `/network/geojson` | GeoJSON representation of corridor topology |

---

## 5. Discrete-Event Simulation & Scenarios (`/simulation`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/simulation/status` | Current clock time, acceleration factor, train count |
| `POST` | `/simulation/control` | Control engine: `start`, `pause`, `resume`, `accelerate`, `step`, `reset` |
| `GET` | `/simulation/snapshot` | Live synchronized digital twin snapshot |
| `POST` | `/simulation/scenarios`| Creates and runs custom scenario with 3-tier comparison |
| `POST` | `/simulation/what-if` | Executes counterfactual what-if perturbation branch |
| `POST` | `/simulation/replay/record` | Captures digital twin timeline slice |
| `GET` | `/simulation/replay/scrub` | Scrubs historical simulation replay buffer |

### Example: Scenario Injection with Baseline Comparison
```bash
curl -X POST http://localhost:8000/simulation/scenarios \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Track 4 Switch Fault",
    "scenario_type": "TRACK_CLOSURE",
    "description": "Simulated turnout lock failure on main track segment 4",
    "parameters": {"track_id": "trk_04", "duration_minutes": 35}
  }'
```

---

## 6. Real-Time Conflict Detection (`/conflicts`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/conflicts` | Lists active and predicted spatial/temporal conflicts |
| `GET` | `/conflicts/{id}` | Detailed conflict report with causal factors |
| `POST` | `/conflicts/{id}/resolve`| Applies resolution strategy (`HOLD_TRAIN`, `REROUTE`, `REASSIGN_PLATFORM`) |

---

## 7. Optimization Engines (`/optimization`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/optimization/route` | Computes Dijkstra, A*, Floyd-Warshall, Multi-Objective, Genetic Algorithm, Particle Swarm, or Simulated Annealing routes |
| `GET`  | `/optimization/runs` | Queries historical optimization runs with delay & energy benchmark audit telemetry |
| `POST` | `/optimization/schedule` | Generates conflict-free headway timetable schedule |
| `POST` | `/optimization/platforms`| Solves platform allocation to eliminate dwell conflicts |
| `POST` | `/optimization/reschedule`| Solves dynamic rescheduling under active disruptions |
| `POST` | `/optimization/eco-driving`| Generates energy-efficient coasting & regenerative speed profile |
| `POST` | `/optimization/rl/train` | Triggers background DQN/PPO training loop with safety metrics |
| `POST` | `/optimization/rl/dispatch` | Evaluates and dispatches an RL action protected by Safety Shield |
| `GET`  | `/optimization/rl/runs` | Queries historical RL training runs and convergence curves |

---

## 8. Multi-Physics & Rolling Stock Dynamics (`/physics`)

| Method | Path | Description |
|---|---|---|
| `GET`  | `/physics/consists` | Catalogs industrial train consists (HST, EMU, Heavy Haul Freight) |
| `POST` | `/physics/simulate-adhesion` | Solves Polach wheel-rail contact mechanics, adhesion envelope, and WSP |
| `POST` | `/physics/simulate-braking` | Simulates UIC brake pipe acoustic wave propagation and in-train coupler forces |
| `POST` | `/physics/simulate-catenary`| Solves 25kV AC catenary power flow, pantograph voltage drops, and regenerative receptivity |

---

## 8. AI Models & Model Registry (`/models`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/models` | Catalogs all AI/ML models in the registry |
| `GET` | `/models/{id}` | Model metadata, feature list, and performance metrics |
| `POST` | `/models/{id}/predict/delay` | Multi-horizon delay prediction (5m to 60m) |
| `POST` | `/models/{id}/predict/congestion` | Spatial bottleneck congestion risk scoring |
| `POST` | `/models/{id}/predict/demand`| 24-hour diurnal station passenger demand forecasting |
| `POST` | `/models/{id}/train` | Retrains model weights on specified dataset |
| `POST` | `/models/{id}/evaluate` | Benchmark evaluation vs. baseline metrics |
| `GET` | `/models/{id}/versions` | Version history and promotion audit log |

---

## 9. Analytics & Operational Reports (`/analytics` & `/reports`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/kpis` | Real-time punctuality, throughput, and conflict KPIs |
| `GET` | `/analytics/delays` | Aggregated delay distribution across stations/trains |
| `GET` | `/analytics/energy` | Fleet energy consumption and carbon abatement |
| `POST` | `/reports/generate` | Generates operational performance report (PDF/CSV/JSON) |
| `GET` | `/reports/download/{id}` | Downloads compiled report document |

---

## 10. System Health & Observability

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | General operational health check |
| `GET` | `/health/live` | Async Kubernetes liveness probe |
| `GET` | `/health/ready` | Async Kubernetes readiness probe (checks DB, memory, models) |
| `GET` | `/metrics` | Prometheus exposition endpoint with 12 custom metrics |

---

## 11. WebSocket Real-Time Channel (`/ws/live`)

- **URL**: `ws://localhost:8000/ws/live`
- **Protocol**: JSON text frames
- **Frequency**: 1 Hz streaming of train positions, signals, active conflicts, and system KPIs.
- **Client Messages Supported**:
  - `{"type": "subscribe", "channels": ["trains", "conflicts", "metrics"]}`
  - `{"type": "ping"}`
