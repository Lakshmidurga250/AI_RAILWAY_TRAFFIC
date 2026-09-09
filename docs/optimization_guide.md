# Railway Optimization Subsystem Guide

The optimization subsystem integrates classical graph algorithms, multi-objective Pareto optimization, dynamic dispatch rescheduling, platform track assignment, and eco-driving energy profiles to streamline corridor operations.

---

## 1. Graph Routing Algorithms (`optimization/routing/`)

### 1.1 Dijkstra & A* Pathfinders (`dijkstra.py`, `astar.py`)
- **Dijkstra's Algorithm**: Guaranteed shortest-distance pathfinding across directed multi-track corridors.
- **A* Algorithm**: Heuristic-guided pathfinding using Euclidean geospatial distance as an admissible heuristic $h(n)$, reducing graph search node expansions by ~40%.
- **$K$-Shortest Paths**: Computes alternative diversionary paths using Yen's algorithm for dynamic rerouting around track closures.

### 1.2 Multi-Objective Pareto Routing (`multi_objective.py`)
Balances competing operational objectives:
$$\min_{p \in \mathcal{P}} J(p) = w_t \cdot T_{\text{travel}}(p) + w_d \cdot D_{\text{risk}}(p) + w_c \cdot C_{\text{congestion}}(p) + w_e \cdot E_{\text{traction}}(p)$$

Where:
- $w_t = 0.40$: Total journey travel time.
- $w_d = 0.25$: Cumulative downstream delay propagation risk.
- $w_c = 0.20$: Route track occupancy / bottleneck congestion index.
- $w_e = 0.15$: Estimated electrical traction energy consumption.

### 1.3 Floyd-Warshall All-Pairs Engine (`floyd_warshall.py`)
Precomputes all-pairs shortest distance and travel-time matrices across all $N$ stations and junctions in $O(V^3)$ time, enabling $O(1)$ constant-time lookup during real-time conflict detection and dynamic rescheduling.

### 1.4 Metaheuristic Route Solvers (`genetic_algorithm.py`, `particle_swarm.py`, `simulated_annealing.py`)
- **Genetic Algorithm (GA)**: Evolves candidate route sequences across generations with tournament selection, crossover at shared topological junction nodes, and diversity mutations.
- **Particle Swarm Optimization (PSO)**: Swarm particles explore route space using cognitive memory ($p_{\text{best}}$) and global social best ($g_{\text{best}}$) velocity guidance.
- **Simulated Annealing (SA)**: Probabilistic hill-climbing using Boltzmann-Gibbs Metropolis acceptance criterion to escape local congestion optima during corridor re-routing.

---

## 2. Dynamic Timetable Scheduling (`optimization/scheduling/`)

- **Implementation**: `optimization/scheduling/timetable.py`
- **Headway Spacing Invariant**: Enforces a strict minimum temporal headway $\Delta t \ge 180 \text{ s}$ and spatial buffer $d \ge 2.0 \text{ km}$ between consecutive trains on identical track blocks.
- **Priority-Driven Sequencing**: Higher-priority services (e.g., Express, High-Speed) are allocated precedence windows over regional or freight traffic during schedule conflicts.

---

## 3. Dynamic Rescheduling & Disruption Recovery (`optimization/rescheduling/`)

- **Implementation**: `optimization/rescheduling/rescheduler.py`
- **Autonomous Recovery Actions**:
  - Automatically identifies trains impacted by sudden track closures, signal interlocking failures, or emergency speed restrictions.
  - Generates conflict-free diversionary routes and adjusted station dwell schedules.
  - Multi-tier benchmark comparison:
    - **Delay Reduction**: Typically 30–45% delay reduction over unmanaged baseline.
    - **Cascading Conflicts**: Prevents gridlock deadlocks on single-track bottlenecks.
    - **Passenger Delay Hours**: Minimizes passenger delay impact across major interchange hubs.

---

## 4. Platform Assignment Optimization (`optimization/platforms/`)

- **Implementation**: `optimization/platforms/assigner.py`
- Formulated as a constrained assignment problem:
  - **Hard Constraints**: Train physical length $\le$ platform length; train electrification status matches platform catenary; platform must be unoccupied during train dwell window $[\text{arr} - \tau, \text{dep} + \tau]$.
  - **Soft Objectives**: Minimize passenger walking distance for interchange transfers and distribute passenger volume evenly across station concourses.

---

## 5. Eco-Driving & Traction Energy Optimization (`ai/energy/`)

- **Implementation**: `ai/energy/model.py`
- **Coasting Phase Optimization**: Computes optimal acceleration, cruising, coasting (power cut), and regenerative braking phases along varying track gradients.
- **Regenerative Braking Recovery**: Recovers up to 35% of train kinetic energy back into the substation catenary grid during deceleration.
- **Carbon Abatement**: Converts saved kilowatt-hours into metric tons of $\text{CO}_2$ abated based on grid emission factors ($0.45 \text{ kg CO}_2 / \text{kWh}$).

---

## 6. Optimization Audit & Telemetry Repository (`backend/repositories/optimization_repository.py`)

- **Persistence Layer**: Tracks every execution of route search, timetable rescheduling, and eco-driving profile calculation in the `optimization_runs` database table.
- **Audit Metrics**:
  - `baseline_delay_minutes` vs. `optimized_delay_minutes` & `delay_reduction_percentage`
  - `baseline_energy_kwh` vs. `optimized_energy_kwh` & `energy_savings_percentage`
  - `conflicts_resolved` & `execution_time_ms`
- **Query Endpoint**: `GET /optimization/runs` provides searchable telemetry filtered by optimization type (`ROUTING`, `RESCHEDULING`, `PLATFORM`, `ECO_DRIVING`).
