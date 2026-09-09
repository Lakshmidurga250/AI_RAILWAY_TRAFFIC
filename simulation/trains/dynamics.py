"""Train Kinematics and Energy Dynamics Engine."""
import math
from typing import Tuple

class TrainDynamics:
    """Physics model calculating traction, resistance, braking, and energy consumption."""
    
    # Davis equation empirical coefficients: R = A + B*v + C*v^2
    # Standard passenger EMU / High Speed Train coefficients
    DEFAULT_A = 2.5     # Mechanical resistance (N/kN)
    DEFAULT_B = 0.035   # Rolling resistance & flange friction (N/(kN * km/h))
    DEFAULT_C = 0.0018  # Aerodynamic drag (N/(kN * (km/h)^2))
    GRAVITY = 9.81      # m/s^2

    @classmethod
    def calculate_resistance_force(
        cls,
        mass_tons: float,
        speed_kmh: float,
        gradient_percent: float = 0.0,
        curve_radius_m: float = 0.0
    ) -> float:
        """Calculate total resistive force in Newtons."""
        weight_kn = mass_tons * cls.GRAVITY
        v = max(0.0, speed_kmh)
        
        # Davis resistance per kN
        r_davis_per_kn = cls.DEFAULT_A + (cls.DEFAULT_B * v) + (cls.DEFAULT_C * (v ** 2))
        r_davis_n = r_davis_per_kn * weight_kn
        
        # Gradient resistance (1% gradient = ~9.81 N/kN)
        # Force = m * g * sin(theta) ~ m * g * (gradient / 100)
        r_gradient_n = weight_kn * (gradient_percent / 100.0) * 1000.0  # N
        
        # Curve resistance (Roeckl formula: ~650 / (R - 55) N/kN)
        r_curve_n = 0.0
        if curve_radius_m > 55.0:
            r_curve_n = (650.0 / (curve_radius_m - 55.0)) * weight_kn
            
        total_resistance = r_davis_n + r_gradient_n + r_curve_n
        return total_resistance

    @classmethod
    def step_kinematics(
        cls,
        current_speed_kmh: float,
        target_speed_kmh: float,
        max_acceleration_ms2: float,
        max_braking_ms2: float,
        dt_seconds: float,
        mass_tons: float,
        gradient_percent: float = 0.0,
        regenerative_efficiency: float = 0.35
    ) -> Tuple[float, float, float, float]:
        """Calculates new speed (km/h), distance traveled (km), energy consumed (kWh), and regenerated energy (kWh).
        
        Returns:
            (new_speed_kmh, distance_km, energy_consumed_kwh, regenerated_kwh)
        """
        current_v_ms = (current_speed_kmh * 1000.0) / 3600.0
        target_v_ms = (target_speed_kmh * 1000.0) / 3600.0
        
        # Determine acceleration or deceleration required
        speed_diff = target_v_ms - current_v_ms
        is_braking = speed_diff < -0.01
        
        if speed_diff > 0.01:
            # Accelerating
            chosen_a_ms2 = min(max_acceleration_ms2, speed_diff / max(0.01, dt_seconds))
        elif is_braking:
            # Braking
            chosen_a_ms2 = max(-max_braking_ms2, speed_diff / max(0.01, dt_seconds))
        else:
            chosen_a_ms2 = 0.0
            
        new_v_ms = max(0.0, current_v_ms + (chosen_a_ms2 * dt_seconds))
        avg_v_ms = (current_v_ms + new_v_ms) / 2.0
        new_speed_kmh = (new_v_ms * 3600.0) / 1000.0
        
        distance_m = avg_v_ms * dt_seconds
        distance_km = distance_m / 1000.0
        
        # Power & Energy computations
        avg_speed_kmh = (current_speed_kmh + new_speed_kmh) / 2.0
        resistance_n = cls.calculate_resistance_force(mass_tons, avg_speed_kmh, gradient_percent)
        inertial_force_n = (mass_tons * 1000.0) * chosen_a_ms2
        
        energy_consumed_kwh = 0.0
        regenerated_kwh = 0.0
        
        if chosen_a_ms2 >= 0:
            # Tractive effort must overcome inertia + resistance
            tractive_force_n = max(0.0, inertial_force_n + resistance_n)
            power_watts = tractive_force_n * avg_v_ms
            # Auxiliaries baseline consumption (HVAC, lighting ~ 40 kW)
            aux_power_watts = 40_000.0
            total_power_watts = power_watts + aux_power_watts
            energy_consumed_kwh = (total_power_watts * dt_seconds) / 3_600_000.0
        else:
            # Braking: regenerative brake recovers kinetic energy
            # Net braking force applied:
            braking_force_n = abs(inertial_force_n) - max(0.0, resistance_n)
            if braking_force_n > 0:
                brake_power_watts = braking_force_n * avg_v_ms
                regenerated_kwh = (brake_power_watts * dt_seconds * regenerative_efficiency) / 3_600_000.0
            # Aux power still runs
            aux_power_watts = 40_000.0
            energy_consumed_kwh = (aux_power_watts * dt_seconds) / 3_600_000.0

        return new_speed_kmh, distance_km, energy_consumed_kwh, regenerated_kwh
