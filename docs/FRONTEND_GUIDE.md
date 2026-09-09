# Operations Control Center (Frontend) Architecture & Guide

The system features an enterprise-grade, cyber-dark glassmorphic **Operations Control Center** implemented as an ultra-fast zero-latency Single Page Application (SPA) served directly from FastAPI (`backend/static/index.html`) alongside a modern React/Vite development stack in `frontend/`.

---

## 1. Visual Design & Aesthetic Philosophy

- **Cyber-Dark Theme**: Deep slate/navy dark mode (`#0b0f19` background) optimized for 24/7 mission-critical dispatch centers with high contrast and zero eye fatigue.
- **Glassmorphic Paneling**: Frosted backdrop filters (`backdrop-blur-md`, semi-transparent RGBA borders) for visual depth.
- **Dynamic Micro-Animations**: Pulsing train beacons, smooth SVG track paths, animated conflict status badges, and real-time metric counter transitions.
- **Typography & Icons**: Clean modern sans-serif typography with high scannability.

---

## 2. Core Functional Views

The UI is structured around 6 dedicated operational views accessed via the primary navigation sidebar:

### View 1: Corridor Digital Twin (`#view-twin`)
- **Interactive Leaflet SVG Map**: Renders stations, double-track corridors, express bypasses, platform lines, and automatic signals in geographic alignment.
- **Live Fleet Tracking**: Trains are rendered as animated icons displaying current speed (km/h), train ID, service name, and color-coded delay status (Green < 2m, Yellow 2-5m, Red > 5m).
- **Interactive Selection**: Clicking any train or station opens a drill-down telemetry panel showing kinematic speed, tractive power, and timetabled stop progression.

### View 2: Conflict Arbiter Queue (`#view-conflicts`)
- Real-time tabular and card queue of detected spatial headway violations, junction contentions, and opposite-direction track risks.
- One-click dispatcher resolution triggers: `Hold Preceding Train`, `Divert to Bypass Loop`, or `Reassign Platform`.

### View 3: AI Model Registry & Lifecycle (`#view-models`)
- Interactive registry cards displaying active AI models (Multi-Horizon Delay, Bottleneck Congestion, Passenger Demand, RL Dispatcher).
- Interactive actions per model:
  - **Retrain**: Dispatches asynchronous training jobs with custom hyperparameters.
  - **Benchmark Evaluate**: Runs model against benchmark validation sets and computes $R^2$, MAE, RMSE vs. baseline.
  - **Version History**: Modal view showing historical releases, dataset lineages, and status transitions (`ACTIVE`, `VALIDATED`, `RETIRED`).

### View 4: Scenario Builder & Baseline Comparator (`#view-scenarios`)
- **Custom Disruption Injector**: Form for injecting track closures, train delays, signal failures, and passenger surges.
- **6-Card Multi-Tier Comparative Benchmark**: Computes and visually contrasts three operational tiers:
  1. *Unmanaged Baseline*
  2. *Standard Heuristic Dispatching*
  3. *AI-Optimized Multi-Objective Plan*
- Displays percentage improvements for Delay Reduction, Conflicts Avoided, Throughput Gain, Peak Delay Abatement, Passenger-Hour Savings, and Energy Conserved.

### View 5: System Observability & Telemetry (`#view-observability`)
- Live Kubernetes Liveness (`/health/live`) and Readiness (`/health/ready`) probe health statuses with live HTTP latency.
- Prometheus Scraper status and instantaneous counters:
  - HTTP request volume & average latency
  - Active trains on network
  - Simulation throughput (steps/sec)
  - Active vs. resolved conflicts
  - AI inference throughput & duration
  - Optimization run frequency

### View 6: Operational Analytics & Reports (`#view-reports`)
- Executive KPI cards: Fleet Punctuality %, Total Delay Minutes, Active Bottlenecks, Cumulative Energy (MWh), and $\text{CO}_2$ Abatement.
- One-click operational report generation (PDF/CSV/JSON).

---

## 3. Real-Time WebSocket Channel (`/ws/live`)

The frontend establishes a resilient WebSocket connection with automatic exponential-backoff reconnection:
- **Streaming Rate**: 1 update per second.
- **Payload**: Full digital twin state snapshot containing updated train coordinates, speeds, current track allocations, signal states, and conflict alerts.
- **Zero Polling**: All map markers and KPI counters update reactively upon receiving WebSocket frames.

---

## 4. Running the Frontend

- **Integrated Mode (Fastest)**:
  Run the backend:
  ```bash
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
  ```
  Open your browser to `http://localhost:8000`.

- **React / Vite Developer Server**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Runs Vite dev server with Hot Module Replacement on `http://localhost:5173`.
