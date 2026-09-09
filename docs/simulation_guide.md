# Railway Simulation & Digital Twin Architecture Guide

The simulation subsystem provides a discrete-event and continuous-step railway simulator that accurately models physical train kinematics, 4-aspect block signaling, station dwell behavior, junction switch alignments, conflict detection, what-if counterfactual branching, and historical timeline replay.

---

## 1. Simulation Engine Architecture

```
                        ┌───────────────────────────────┐
                        │   Simulation Clock & Ticks    │
                        │ (1x, 5x, 15x, 30x, 60x Speed) │
                        └───────────────┬───────────────┘
                                        │
        ┌───────────────────────────────┼───────────────────────────────┐
        ▼                               ▼                               ▼
┌───────────────┐               ┌───────────────┐               ┌───────────────┐
│ Train Physics │               │ Block Signals │               │ Conflict Arb  │
│  & Davis Drag │               │ & Interlock   │               │ & Deadlocks   │
└───────┬───────┘               └───────┬───────┘               └───────┬───────┘
        │                               │                               │
        └───────────────────────────────┼───────────────────────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │    Synchronized Event Bus     │
                        │ (Event Sourcing & Replay Log) │
                        └───────────────┬───────────────┘
                                        ▼
                        ┌───────────────────────────────┐
                        │   Digital Twin Shadow State   │
                        │     (Live /ws/live Stream)    │
                        └───────────────────────────────┘
```

---

## 2. Train Dynamics & Kinematics (`simulation/trains/dynamics.py`)

Train motion is governed by Newtonian kinematics combined with the empirical **Davis Formula for Rolling and Aerodynamic Resistance**:

$$F_{\text{net}} = F_{\text{traction}} - R_{\text{total}} - m \cdot g \cdot \sin(\theta) - R_{\text{curve}}$$

$$R_{\text{total}} = (A + B \cdot v + C \cdot v^2) \cdot m \cdot g$$

Where:
- $A$: Mechanical rolling resistance coefficient (bearing and track roughness).
- $B$: Flange friction and mechanical transmission coefficient.
- $C$: Aerodynamic drag coefficient proportional to cross-sectional area and streamline shape.
- $\theta$: Track gradient inclination angle.
- $v$: Current velocity in $\text{m/s}$.

The kinematic step calculates instantaneous acceleration, velocity, spatial position along the track segment, power draw ($\text{kW}$), and regenerative braking energy recovery ($\text{kWh}$).

---

## 3. Four-Aspect Automated Block Signaling (`simulation/signals/signaling.py`)

Tracks are divided into discrete blocks governed by 4-aspect signaling:
1. **GREEN**: Next two or more blocks are clear; train may proceed at maximum authorized line speed.
2. **DOUBLE YELLOW**: Next block is clear, but second block is occupied; train must decelerate to approach speed.
3. **YELLOW**: Next block is clear, but immediate subsequent signal is Red; train must prepare to stop.
4. **RED**: Immediate block ahead is occupied or switch is unlocked/misaligned; train must stop before signal post.

---

## 4. Conflict Detection Arbiter (`simulation/conflicts/detector.py`)

The arbiter continuously scans active trajectories at each simulation step to identify:
- **Headway Violations**: Preceding and following trains on the same track within 180 seconds or 2.0 km.
- **Opposite-Direction Deadlocks**: Two trains routed toward each other on a single-track segment without passing siding.
- **Junction Convergences**: Multiple trains converging on an interlocking turnout within a 3-minute collision window.
- **Platform Contention**: Overlapping station dwell windows on the same platform.

---

## 5. What-If Branching & Historical Replay

### What-If Counterfactual Branching (`simulation/engine/what_if.py`)
Allows dispatchers to clone the current digital twin state and simulate hypothetical perturbations (e.g. "What if Track 2 closes for 45 minutes?" or "What if Train 102 is delayed by 20 minutes?") in a sandboxed execution branch without affecting the live production network.

### Historical Replay Buffer (`simulation/engine/replay.py`)
Records time-series simulation state snapshots into a circular buffer. Dispatchers can scrub backwards and forwards through historical incident timelines to analyze root causes and post-incident response.

---

## 6. Headless Simulation Worker (`simulation/engine/worker.py`)

For high-throughput continuous simulations without web server overhead, the headless simulation worker runs as a standalone daemon or within Docker (`docker/Dockerfile.worker`):

```bash
# Run headless simulation worker
python -m simulation.engine.worker --interval 1.0 --acceleration 5.0
```
