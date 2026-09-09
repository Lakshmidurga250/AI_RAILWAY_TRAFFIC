# Platform Architecture & Subsystem Specification

## 1. High-Level Architecture

The **AI Railway Traffic Optimization & Intelligent Train Management System** is structured as an event-driven, micro-modular monorepo where real-time discrete simulation, predictive machine learning, mathematical optimization, and operational telemetry converge through a synchronized **Digital Twin**.

```
Railway Infrastructure (NetworkX Directed Graph)
               │
               ▼
Discrete-Event Kinematic Simulator (Davis Formula, 4-Aspect Signaling, Interlocking)
               │
               ▼
Event Bus (Event-Sourcing: TRAIN_DEPARTED, CONFLICT_DETECTED, SIGNAL_CHANGED)
               │
               ▼
Digital Twin Real-Time Shadow (State Synchronization)
               │
      ┌────────┴────────────────────────┬────────────────────────┐
      ▼                                 ▼                        ▼
AI Predictive Models            Conflict Arbiter           Optimization Engines
- Multi-Horizon Delay           - Headway Violation        - Multi-Objective Pareto
- Bottleneck Congestion         - Opposite Track Risk      - Headway Timetable Scheduler
- Passenger Surge Flows         - Junction Convergence     - Dynamic Rescheduler
- Reinforcement Learning Policy - Platform Overlap         - Eco-Driving Speed Profiles
      │                                 │                        │
      └────────────────┬────────────────┴────────────────────────┘
                       ▼
            Explainable AI (XAI)
            - Feature Attribution (SHAP-Proxy)
            - Counterfactual Mitigation
                       │
                       ▼
            FastAPI Production Backend
            - REST Endpoints (12 Resource Routers)
            - Real-Time WebSocket Channel (/ws/live)
            - Prometheus Metrics (/metrics)
                       │
                       ▼
     Operations Control Center Dashboard (SPA)
     - Interactive Leaflet SVG Track Map
     - Live Animated Fleet Telemetry
     - Scenario Builder & What-If Comparator
     - AI Model Registry & Analytics
```

---

## 2. Subsystem Specifications

### 2.1. Network Infrastructure & Graph Engine
- **Module**: `simulation/network/`
- **Topology**: Models high-speed and intercity corridors using NetworkX `MultiDiGraph`.
- **Elements**:
  - `StationNode`: Platforms, passenger capacity, coordinates, zone assignment.
  - `TrackEdge`: Distance (km), max speed (km/h), gradient (%), electrification status, bidirectional flags, dynamic maintenance closures.
  - `SignalElement`: 4-aspect block signaling (GREEN, DOUBLE_YELLOW, YELLOW, RED).
  - `SwitchElement`: Junction turnouts with safety interlocking and lockout tracking.

### 2.2. Physics & Kinematics Engine
- **Module**: `simulation/trains/dynamics.py`
- **Davis Formula for Total Resistance**:
  $$R_{total} = (A + B \cdot v + C \cdot v^2) \cdot m \cdot g + m \cdot g \cdot \sin(\theta) + R_{curve}$$
- **Kinematic Step**: Computes tractive effort, inertial forces, speed evolution, and regenerative braking recovery (35% standard energy recovery efficiency).

### 2.3. Real-Time Conflict Detection
- **Module**: `simulation/conflicts/detector.py`
- **Algorithms**:
  - Spatial-temporal headway monitoring (minimum 180s time / 2.0km spatial buffer).
  - Opposite-direction detection on single-track sections (CRITICAL deadlock alert).
  - Multi-train junction convergence forecasting within 3-minute collision horizons.
  - Platform allocation contention.

### 2.4. Machine Learning & Predictive Pipelines
- **Module**: `ai/`
- **Multi-Horizon Delay Predictor**:
  - Horizons: 5m, 10m, 15m, 30m, 60m.
  - Ensemble: Gradient Boosting Regressor + Random Forest.
  - Validation: MAE 1.12m, RMSE 1.64m, $R^2 = 0.88$.
- **Congestion Predictor**:
  - Evaluates track occupancy ratio, platform utilization, and junction throughput.
- **Passenger Demand Forecaster**:
  - 24-hour diurnal volume projection with anomaly detection.
- **Reinforcement Learning Dispatch**:
  - Gymnasium-compatible `RailwayGymEnv` with DQN policy.
  - Reward function: Conflict avoidance + delay reduction + throughput bonus.

### 2.5. Mathematical & Heuristic Optimization
- **Module**: `optimization/`
- **Routing**: Dijkstra, A*, and Multi-Objective Pareto Router (travel time, congestion, energy, conflicts).
- **Scheduling**: Priority-constrained headway timetable generator.
- **Dynamic Rescheduling**: Autonomous disruption recovery (track closure, signal failures) with verified baseline vs. optimized comparison.
- **Energy Optimization**: Coasting and regenerative braking trajectory generation yielding 15-20% energy savings.
