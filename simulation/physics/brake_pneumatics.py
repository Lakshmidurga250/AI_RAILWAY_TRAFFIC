"""Train Pneumatic Brake Pipe Propagation and In-Train Coupler Force Model.

Simulates acoustic pressure wave propagation through the continuous brake pipe (UIC 540),
distributed brake cylinder pressure buildup across wagons, and resulting longitudinal
coupler buff (compression) and draft (tension) forces.
"""
import math
from typing import List, Dict, Any, Optional


class BrakePneumaticModel:
    """Acoustic brake pipe propagation and cylinder fill dynamics."""

    NOMINAL_PIPE_PRESSURE_BAR = 5.0   # Standard UIC charged running pressure
    EMERGENCY_VENT_RATE_BAR_S = 2.5   # Pressure vent rate at driver's valve
    ACOUSTIC_WAVE_SPEED_MS = 260.0    # Pressure wave propagation velocity in air pipe (m/s)

    # Time constants for brake cylinder filling (tau_fill in seconds)
    FILL_TIME_PASSENGER_S = 3.5       # UIC 'P' mode (Rapid response)
    FILL_TIME_FREIGHT_S = 22.0        # UIC 'G' mode (Slow progressive fill to reduce shock)

    @classmethod
    def simulate_brake_application(
        cls,
        consist_length_m: float,
        wagon_count: int,
        target_pipe_pressure_bar: float,
        elapsed_time_s: float,
        brake_mode: str = "PASSENGER"
    ) -> Dict[str, Any]:
        """Simulate pneumatic wave propagation and cylinder pressures along train length.

        Parameters:
            consist_length_m: Total length of train in meters
            wagon_count: Total number of vehicles/wagons
            target_pipe_pressure_bar: Desired brake pipe pressure (e.g. 3.5 bar for full service, 0 bar for emergency)
            elapsed_time_s: Seconds elapsed since brake valve was opened
            brake_mode: "PASSENGER" ('P') or "FREIGHT" ('G')

        Returns:
            Dict containing wagon-by-wagon pressure distribution and effective braking percentage.
        """
        tau_fill = cls.FILL_TIME_PASSENGER_S if brake_mode.upper() == "PASSENGER" else cls.FILL_TIME_FREIGHT_S
        pressure_reduction = max(0.0, cls.NOMINAL_PIPE_PRESSURE_BAR - target_pipe_pressure_bar)
        is_emergency = target_pipe_pressure_bar <= 0.2

        # Maximum brake cylinder pressure is typically 3.8 bar when pipe drops by 1.5 bar
        max_bc_pressure = min(3.8, (pressure_reduction / 1.5) * 3.8)

        wagon_states = []
        wagon_spacing_m = consist_length_m / max(1, wagon_count)

        total_braking_fraction = 0.0

        for i in range(wagon_count):
            dist_from_loco_m = (i + 0.5) * wagon_spacing_m
            # Delay before acoustic wave reaches this wagon
            wave_delay_s = dist_from_loco_m / cls.ACOUSTIC_WAVE_SPEED_MS

            effective_time_s = max(0.0, elapsed_time_s - wave_delay_s)
            if effective_time_s <= 0.0:
                # Wave has not reached this vehicle yet
                bc_pressure = 0.0
                pipe_p = cls.NOMINAL_PIPE_PRESSURE_BAR
            else:
                # Cylinder fills exponentially once wave arrives
                fill_fraction = 1.0 - math.exp(-effective_time_s / tau_fill)
                bc_pressure = max_bc_pressure * fill_fraction
                pipe_p = max(target_pipe_pressure_bar, cls.NOMINAL_PIPE_PRESSURE_BAR - (pressure_reduction * min(1.0, effective_time_s / 1.5)))

            braking_fraction = bc_pressure / 3.8 if max_bc_pressure > 0 else 0.0
            total_braking_fraction += braking_fraction

            wagon_states.append({
                "wagon_index": i + 1,
                "distance_from_loco_m": round(dist_from_loco_m, 1),
                "wave_delay_seconds": round(wave_delay_s, 3),
                "brake_pipe_pressure_bar": round(pipe_p, 2),
                "brake_cylinder_pressure_bar": round(bc_pressure, 2),
                "braking_effort_percentage": round(braking_fraction * 100.0, 1)
            })

        avg_braking_pct = round((total_braking_fraction / max(1, wagon_count)) * 100.0, 1)

        return {
            "consist_length_m": consist_length_m,
            "wagon_count": wagon_count,
            "elapsed_time_seconds": elapsed_time_s,
            "brake_mode": brake_mode.upper(),
            "target_pipe_pressure_bar": target_pipe_pressure_bar,
            "is_emergency_application": is_emergency,
            "total_propagation_time_seconds": round(consist_length_m / cls.ACOUSTIC_WAVE_SPEED_MS, 3),
            "average_train_braking_percentage": avg_braking_pct,
            "wagons": wagon_states
        }


class CouplerForceAnalyzer:
    """Calculates longitudinal buff (compression) and draft (tension) forces between vehicles."""

    BUFF_LIMIT_KN = 1400.0   # European standard maximum allowable buff force before jackknife risk
    DRAFT_LIMIT_KN = 1000.0  # Maximum draft force before coupler knuckle fracture risk

    @classmethod
    def compute_in_train_forces(
        cls,
        wagon_masses_tons: List[float],
        wagon_braking_efforts_pct: List[float],
        nominal_decel_ms2: float = 1.0
    ) -> Dict[str, Any]:
        """Compute inter-vehicle coupler forces during non-uniform braking.

        Parameters:
            wagon_masses_tons: Mass of each vehicle from head to rear
            wagon_braking_efforts_pct: Instantaneous braking effort (0 to 100%) on each vehicle
            nominal_decel_ms2: Full deceleration achievable at 100% brake effort

        Returns:
            Summary of peak coupler forces and safety margins.
        """
        n = len(wagon_masses_tons)
        if n <= 1:
            return {"coupler_forces_kn": [], "max_buff_kn": 0.0, "max_draft_kn": 0.0, "status": "SAFE"}

        # Calculate individual vehicle decelerations
        vehicle_decels = [
            (pct / 100.0) * nominal_decel_ms2 for pct in wagon_braking_efforts_pct
        ]

        # In-train coupler forces by progressive integration from tail to head
        # F_coupler[i] represents the force between wagon i and wagon i+1
        # Positive = Tension (Draft), Negative = Compression (Buff)
        coupler_forces_kn = []
        total_mass = sum(wagon_masses_tons)
        total_braking_force_kn = sum(m * d for m, d in zip(wagon_masses_tons, vehicle_decels))
        mean_accel = total_braking_force_kn / max(1.0, total_mass)

        # Cumulative difference between trailing mass acceleration and vehicle force
        accumulated_force = 0.0
        for i in range(n - 1):
            diff_force = wagon_masses_tons[i] * (mean_accel - vehicle_decels[i])
            accumulated_force += diff_force
            coupler_forces_kn.append(round(accumulated_force, 1))

        max_buff = max(0.0, -min(coupler_forces_kn)) if coupler_forces_kn else 0.0
        max_draft = max(0.0, max(coupler_forces_kn)) if coupler_forces_kn else 0.0

        is_derailment_risk = max_buff > cls.BUFF_LIMIT_KN
        is_break_apart_risk = max_draft > cls.DRAFT_LIMIT_KN

        status = "SAFE"
        if is_derailment_risk:
            status = "CRITICAL_BUFF_EXCEEDED"
        elif is_break_apart_risk:
            status = "CRITICAL_DRAFT_EXCEEDED"
        elif max_buff > 0.8 * cls.BUFF_LIMIT_KN:
            status = "WARNING_HIGH_BUFF"

        return {
            "vehicle_count": n,
            "coupler_forces_kn": coupler_forces_kn,
            "max_buff_compression_kn": round(max_buff, 1),
            "max_draft_tension_kn": round(max_draft, 1),
            "buff_safety_margin_percentage": round(max(0.0, (1.0 - (max_buff / cls.BUFF_LIMIT_KN)) * 100.0), 1),
            "draft_safety_margin_percentage": round(max(0.0, (1.0 - (max_draft / cls.DRAFT_LIMIT_KN)) * 100.0), 1),
            "derailment_risk": is_derailment_risk,
            "status": status
        }
