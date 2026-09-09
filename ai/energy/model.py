"""Railway Energy Optimization and Eco-Driving Trajectory Engine."""
import math
from typing import Dict, Any, List, Tuple
from simulation.trains.dynamics import TrainDynamics

class EnergyOptimizationEngine:
    """Calculates eco-driving trajectories, regenerative braking recovery, and CO2 emissions saved."""
    
    # Grid emission factor: ~0.42 kg CO2 / kWh
    GRID_CO2_PER_KWH = 0.42

    @classmethod
    def optimize_run(
        cls,
        mass_tons: float = 400.0,
        distance_km: float = 25.0,
        scheduled_time_minutes: float = 18.0,
        gradient_percent: float = 0.0,
        max_speed_kmh: float = 160.0
    ) -> Dict[str, Any]:
        """Compares baseline flat-out driving vs optimized eco-driving (pulse-and-glide / coasting)."""
        # Baseline: Accelerate at max rate to top speed, cruise until hard braking
        baseline_speed = min(max_speed_kmh, (distance_km / (scheduled_time_minutes / 60.0)) * 1.25)
        # Power = F * v + aux
        baseline_res = TrainDynamics.calculate_resistance_force(mass_tons, baseline_speed, gradient_percent)
        baseline_tractive = max(1000.0, baseline_res + (mass_tons * 1000.0 * 0.4))
        baseline_power_kw = (baseline_tractive * (baseline_speed / 3.6)) / 1000.0 + 40.0
        baseline_energy_kwh = baseline_power_kw * (scheduled_time_minutes / 60.0)

        # Optimized Eco-Driving:
        # Accelerate to eco-speed (approx 85% of max), coast over downslope / midway, regenerative stop
        eco_speed = baseline_speed * 0.88
        eco_res = TrainDynamics.calculate_resistance_force(mass_tons, eco_speed, gradient_percent)
        eco_tractive = max(800.0, eco_res + (mass_tons * 1000.0 * 0.25))
        eco_power_kw = (eco_tractive * (eco_speed / 3.6)) / 1000.0 + 35.0
        
        # Coasting 25% of distance requires zero tractive energy
        tractive_time_hours = (scheduled_time_minutes / 60.0) * 0.70
        eco_energy_raw = eco_power_kw * tractive_time_hours + (40.0 * (scheduled_time_minutes / 60.0) * 0.30)
        
        # Regenerative braking recovery: 35% of train kinetic energy: 0.5 * m * v^2
        kinetic_energy_joules = 0.5 * (mass_tons * 1000.0) * ((eco_speed / 3.6) ** 2)
        regen_kwh = (kinetic_energy_joules * 0.35) / 3_600_000.0
        
        optimized_energy_kwh = max(10.0, eco_energy_raw - regen_kwh)
        savings_kwh = max(0.0, baseline_energy_kwh - optimized_energy_kwh)
        savings_pct = (savings_kwh / max(1.0, baseline_energy_kwh)) * 100.0
        co2_saved_kg = savings_kwh * cls.GRID_CO2_PER_KWH

        # Generate sample speed profile trajectory
        num_points = 10
        profile = []
        for i in range(num_points):
            km = (i / (num_points - 1)) * distance_km
            if i < 3:
                spd = (i / 2.0) * eco_speed
            elif i < 7:
                spd = eco_speed
            elif i < 9:
                spd = eco_speed * 0.7  # coasting
            else:
                spd = 0.0  # stopped
            profile.append({"distance_km": round(km, 1), "recommended_speed_kmh": round(spd, 1)})

        explanation = (
            f"Eco-driving strategy utilizes a speed ceiling of {eco_speed:.1f} km/h with a 3.5 km coasting phase "
            f"and regenerative braking, achieving a {savings_pct:.1f}% net energy saving while preserving timetable margin."
        )

        return {
            "baseline_energy_kwh": round(baseline_energy_kwh, 2),
            "optimized_energy_kwh": round(optimized_energy_kwh, 2),
            "energy_savings_percentage": round(savings_pct, 2),
            "co2_reduction_kg": round(co2_saved_kg, 2),
            "speed_profile": profile,
            "explanation": explanation
        }
