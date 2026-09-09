"""Energy Optimization Model Unit Tests."""
from ai.energy.model import EnergyOptimizationEngine

def test_eco_driving_energy_optimization():
    res = EnergyOptimizationEngine.optimize_run(
        mass_tons=450.0,
        distance_km=30.0,
        scheduled_time_minutes=20.0,
        gradient_percent=0.1,
        max_speed_kmh=160.0
    )
    assert res["baseline_energy_kwh"] > res["optimized_energy_kwh"]
    assert res["energy_savings_percentage"] > 5.0
    assert res["co2_reduction_kg"] > 0.0
    assert len(res["speed_profile"]) >= 5
    assert "explanation" in res
