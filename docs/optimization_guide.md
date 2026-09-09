# Railway Optimization Subsystem Guide

## 1. Multi-Objective Route Optimization
- **Implementation**: `optimization/routing/multi_objective.py`
- **Objective Function**:
  $$\min \sum \left( w_t \cdot T_{travel} + w_d \cdot D_{risk} + w_c \cdot C_{congestion} + w_e \cdot E_{traction} \right)$$
- Evaluates $k$-shortest paths using NetworkX graph projections and scores composite Pareto fitness.

---

## 2. Dynamic Rescheduling & Disruption Recovery
- **Implementation**: `optimization/rescheduling/rescheduler.py`
- **Capabilities**:
  - Handles track closures, signal interlocking failures, and severe weather.
  - Automatically identifies affected trains and computes conflict-free detours.
  - Generates verifiable Baseline vs. Optimized comparisons:
    - Delay reduction percentage.
    - Cascading conflicts eliminated.
    - Passenger-delay-hours saved.

---

## 3. Platform Assignment Optimization
- **Implementation**: `optimization/platforms/assigner.py`
- Evaluates platform length constraints, train length compatibility, passenger volume, catenary electrification, and passenger accessibility ratings.

---

## 4. Traction Energy Optimization
- **Implementation**: `ai/energy/model.py`
- Models coasting windows and regenerative braking recovery (up to 35% of train kinetic energy).
- Outputs recommended speed trajectories and estimated metric tons of $\text{CO}_2$ abated.
