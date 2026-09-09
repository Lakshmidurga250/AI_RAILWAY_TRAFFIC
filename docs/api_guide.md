# API Specification & Endpoint Guide

The backend exposes a REST API along with real-time WebSockets under `http://localhost:8000`.

## 1. Authentication & Users (`/auth`)
* `POST /auth/register`: Create a new user (admin/dispatcher/viewer).
* `POST /auth/login`: Authenticate and receive a JWT Bearer token.
* `GET /auth/me`: Get current authenticated user profile.

## 2. Train Fleet Management (`/trains`)
* `GET /trains`: List active and scheduled train fleet with real-time GPS coordinates, speed, delay, priority, and energy metrics.
* `GET /trains/{train_id}`: Get full telemetry and schedule stops for a specific train.
* `POST /trains/{train_id}/priority`: Dynamically update dispatch priority (1 to 10).
* `POST /trains/{train_id}/speed`: Issue speed harmonization command (0 to 300 km/h).

## 3. Network Infrastructure (`/network`, `/stations`)
* `GET /network/graph`: Get full corridor topology in GeoJSON-compatible node/edge format.
* `GET /network/tracks`: List all track blocks, speed limits, gradients, and occupancy.
* `PUT /network/tracks/{track_id}/status`: Toggle maintenance closure or temporary speed restriction.
* `GET /network/signals`: Inspect 4-aspect block signal states.
* `GET /stations`: List stations with platform capacities and live passenger occupancies.

## 4. Simulation Engine (`/simulation`)
* `GET /simulation/status`: Current simulation metrics, speed acceleration factor, and active conflicts.
* `GET /simulation/snapshot`: Complete digital twin state snapshot.
* `POST /simulation/control`: Execute simulation actions (`start`, `pause`, `resume`, `stop`, `accelerate`, `step`, `reset`).
* `GET /simulation/scenarios`: List standard disruption scenarios.
* `POST /simulation/scenarios/{id}/compare`: Run baseline vs optimized what-if benchmark.

## 5. Artificial Intelligence (`/ai`)
* `POST /ai/delay`: Multi-horizon train delay prediction (5m, 10m, 15m, 30m, 60m) with feature attributions.
* `POST /ai/congestion`: Resource congestion score (0.0 to 1.0), severity level, and recommendations.
* `POST /ai/demand`: 24-hour hourly passenger demand forecast with surge alerts.
* `POST /ai/rl/train`: Run DQN dispatch policy training and evaluation against baseline.
* `POST /ai/energy/{train_id}`: Calculate eco-driving trajectory and carbon abatement.
* `GET /ai/models`: List all registered models with version and metrics.

## 6. Optimization (`/optimization`)
* `POST /optimization/route`: Calculate Pareto, A*, or Dijkstra optimal routing.
* `POST /optimization/platform`: Find optimal platform assignment matching train length and accessibility.
* `POST /optimization/schedule`: Generate conflict-free timetable enforcing 3-minute headway buffer.
* `POST /optimization/reschedule`: Execute real-time dynamic rescheduling during track closures.
* `POST /optimization/conflicts/{id}/resolve`: Autonomously mitigate active conflict.

## 7. Conflicts & Safety (`/conflicts`)
* `GET /conflicts`: List active spatial-temporal conflicts.
* `GET /conflicts/history`: Audit log of resolved conflicts.

## 8. Analytics & Reporting (`/analytics`, `/reports`)
* `GET /analytics/dashboard`: Live KPI summary, delay distributions, station occupancies, energy trends.
* `GET /reports/operational?format={json|csv|markdown}`: Daily operational performance audit.
* `GET /reports/safety`: Network safety and conflict resolution audit.
* `GET /reports/energy`: Traction energy consumption and carbon abatement report.

## 9. Real-Time WebSocket (`/ws/live`)
Connect to `ws://localhost:8000/ws/live` for streaming ticks containing train locations, speeds, delays, signal aspect changes, and conflict alerts.
