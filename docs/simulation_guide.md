# Discrete-Event Railway Simulation Guide

## 1. Physical Modeling & Dynamics

The simulator models train movement according to continuous kinematics and the empirical **Davis Equation**:

$$R = A + B \cdot v + C \cdot v^2$$

Where:
* $A$ represents mechanical resistance (flange friction, axle bearing resistance) in $N/kN$.
* $B$ represents rolling resistance in $N / (kN \cdot km/h)$.
* $C$ represents aerodynamic drag coefficient in $N / (kN \cdot (km/h)^2)$.

### Gradient and Curve Resistance
* **Gradient Resistance**: $R_{\text{gradient}} = m \cdot g \cdot \frac{\text{gradient}}{100}$
* **Curve Resistance**: Calculated using the standard Roeckl formula when curvature radius is defined.

## 2. Signaling System

The simulator uses a 4-aspect block signaling hierarchy:
1. **GREEN**: Clear block ahead; train is permitted to travel at maximum permissible track speed.
2. **DOUBLE YELLOW**: Preliminary caution; next signal is at Yellow. Driver prepares to decelerate.
3. **YELLOW**: Caution; next signal is at Red (Danger). Braking required immediately.
4. **RED**: Danger; block occupied. Absolute stop required before signal marker.

## 3. Platform Dwell Dynamics

Platform dwell time is dynamic rather than fixed, computing passenger exchange rates:

$$\text{Dwell Time} = 25\text{s} + \frac{\text{Passengers On} + \text{Passengers Off}}{\text{Number of Doors} \times 1.1}$$

Bounded between 60 seconds (minimum safety dwell) and 300 seconds (congested dwell).

## 4. Simulation Modes
* **Real-time (1x)**: Advances 1 simulation second per real-time second.
* **Accelerated (5x - 60x)**: Fast-forwards operational shifts for dispatch throughput analysis.
* **Step Mode**: Advances discrete increments (e.g. 10s per call) for deterministic algorithmic evaluation.
* **What-If Scenario Simulation**: Injects track closures, signal failures, or weather disruptions and computes baseline vs optimized operational impact.
