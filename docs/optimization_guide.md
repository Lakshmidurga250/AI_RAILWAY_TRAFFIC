# Optimization Systems & Decision-Support Guide

## 1. Multi-Objective Route Optimization

When dispatching trains, the router balances competing operational objectives rather than optimizing distance in isolation:

$$\min \quad J = w_1 \cdot T_{\text{travel}} + w_2 \cdot D_{\text{risk}} + w_3 \cdot C_{\text{congestion}} + w_4 \cdot E_{\text{traction}}$$

Where:
* $T_{\text{travel}}$: Total estimated run time based on track speed limits.
* $D_{\text{risk}}$: Active conflicts along the candidate trajectory.
* $C_{\text{congestion}}$: Average density of trains on constituent blocks.
* $E_{\text{traction}}$: Traction energy required given distance and gradient profiles.

The engine evaluates $k$-shortest paths using Dijkstra, A* with Euclidean heuristics, and Multi-Objective Pareto ranking.

---

## 2. Dynamic Timetable Scheduling

The scheduler enforces strict safety spacing:
* **Headway Constraint**: Departure spacing $\ge 180$ seconds between consecutive trains entering the same track corridor.
* **Precedence Arbitration**: High-priority services (High-Speed / Emergency) are scheduled first; regional and freight services adjust around passenger express slots.

---

## 3. Dynamic Disruption Rescheduling

When a track closure or signal failure occurs:
1. Identifies all active trains scheduled to traverse the blocked block.
2. Re-evaluates graph topology with the affected edge assigned infinite cost ($w = \infty$).
3. Computes detour paths via relief lines or passing loops.
4. Harmonizes speed profiles on the diversion corridor.
5. Quantifies improvement: Compares unmanaged baseline (cascading queue) against optimized rerouting, computing **delay reduction percentage** and **passenger-hours saved**.

---

## 4. Platform Assignment Optimization

Station platform allocation evaluates:
* Train length vs platform physical length ($L_{\text{platform}} \ge L_{\text{train}}$).
* Temporal occupancy windows (ensuring no overlapping dwell).
* Passenger accessibility ratings (proximity to concourse and transfers).
* Overhead catenary availability for electric traction.

---

## 5. Eco-Driving Energy Optimization

Models tractive effort and kinetic recovery:
* Replaces hard braking with planned **coasting phases** prior to station approaches.
* Harvests up to **35% of braking kinetic energy** via regenerative braking, feeding energy back into the distribution grid.
* Reduces traction energy consumption by **15% to 22%** while staying within timetable margin.
