# Railway Simulation & Digital Twin Guide

## Overview
The simulation subsystem provides a discrete-event and continuous-step railway simulator that accurately models physical train motion, block signaling, station dwell times, switch alignment, and cascade delay propagation.

## Key Modules

| Module | File | Purpose |
|---|---|---|
| **Graph Engine** | `simulation/network/graph.py` | Directed multigraph of stations, junctions, and tracks. |
| **Corridor Loader** | `simulation/network/loader.py` | Default 10-station, 20-track double-line mainline. |
| **Train Dynamics** | `simulation/trains/dynamics.py` | Physics kinematics and Davis resistance calculations. |
| **Train Agent** | `simulation/trains/train.py` | State machine governing cruising, braking, and dwelling. |
| **Block Signaling** | `simulation/signals/signaling.py` | 4-aspect automated block signal progression. |
| **Conflict Detector**| `simulation/conflicts/detector.py`| Real-time spatial headway and junction conflict scanner. |
| **Simulation Engine**| `simulation/engine/simulator.py` | Central clock, acceleration controller, and background loop. |
| **Digital Twin** | `simulation/engine/digital_twin.py`| Synchronized live state shadow of the physical network. |

## Simulation Commands via API

```bash
# Start background simulation
curl -X POST http://localhost:8000/simulation/control \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# Accelerate simulation to 15x
curl -X POST http://localhost:8000/simulation/control \
  -H "Content-Type: application/json" \
  -d '{"action": "accelerate", "acceleration_factor": 15.0}'

# Fetch synchronized live snapshot
curl http://localhost:8000/simulation/snapshot
```
