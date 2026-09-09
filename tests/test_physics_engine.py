"""Tests for Multi-Physics Engine: Adhesion, Brake Pneumatics, Catenary, and Consists."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from simulation.physics.wheel_rail_adhesion import WheelRailAdhesionModel, TrackAdhesionCondition
from simulation.physics.brake_pneumatics import BrakePneumaticModel, CouplerForceAnalyzer
from simulation.physics.catenary_power_flow import CatenarySubstationNetwork
from simulation.physics.rolling_stock_consist import RollingStockConsist, ConsistType


@pytest.fixture
def client():
    return TestClient(app)


def test_wheel_rail_adhesion_conditions():
    """Verify Polach adhesion variation across railhead friction conditions."""
    speed = 60.0  # km/h
    slip = 0.018  # optimal creepage

    mu_dry = WheelRailAdhesionModel.calculate_adhesion_coefficient(
        slip_ratio=slip, speed_kmh=speed, condition=TrackAdhesionCondition.DRY_CLEAN
    )
    mu_wet = WheelRailAdhesionModel.calculate_adhesion_coefficient(
        slip_ratio=slip, speed_kmh=speed, condition=TrackAdhesionCondition.WET_RAIN
    )
    mu_leaves = WheelRailAdhesionModel.calculate_adhesion_coefficient(
        slip_ratio=slip, speed_kmh=speed, condition=TrackAdhesionCondition.LEAVES_ON_LINE
    )

    assert mu_dry > mu_wet > mu_leaves
    assert mu_dry >= 0.30
    assert mu_leaves <= 0.10

    # Test sanding enhancement on contaminated rail
    mu_sanded = WheelRailAdhesionModel.calculate_adhesion_coefficient(
        slip_ratio=slip, speed_kmh=speed, condition=TrackAdhesionCondition.LEAVES_ON_LINE, sanding_active=True
    )
    assert mu_sanded > mu_leaves


def test_wheel_slip_protection_wsp():
    """Verify WSP intervention when demanded tractive force exceeds physical friction limit."""
    adhesive_mass_tons = 120.0  # Locomotive weight
    speed_kmh = 40.0

    # Request excessive 400 kN under wet conditions
    res = WheelRailAdhesionModel.evaluate_traction_limit(
        demanded_tractive_force_n=400_000.0,
        adhesive_mass_tons=adhesive_mass_tons,
        speed_kmh=speed_kmh,
        condition=TrackAdhesionCondition.WET_RAIN,
        wsp_enabled=True
    )

    assert res["wheel_slip_detected"] is True
    assert res["wsp_active"] is True
    assert res["actual_force_kn"] < res["demanded_force_kn"]
    assert res["actual_force_kn"] <= res["max_adhesion_force_kn"]


def test_brake_pneumatics_acoustic_wave_propagation():
    """Verify acoustic propagation delay along 400m train brake pipe."""
    consist_length_m = 400.0
    wagon_count = 16

    # 1.0 second after driver initiates emergency brake application (target 0 bar)
    res = BrakePneumaticModel.simulate_brake_application(
        consist_length_m=consist_length_m,
        wagon_count=wagon_count,
        target_pipe_pressure_bar=0.0,
        elapsed_time_s=1.0,
        brake_mode="PASSENGER"
    )

    assert res["consist_length_m"] == 400.0
    assert res["is_emergency_application"] is True
    assert res["total_propagation_time_seconds"] > 1.4  # 400m / 260 m/s = ~1.54s

    wagons = res["wagons"]
    # First wagon should be actively braking
    assert wagons[0]["brake_cylinder_pressure_bar"] > 0.5
    # Rear wagon (delay ~1.5s) should not have received the pressure wave yet at t=1.0s
    assert wagons[-1]["brake_cylinder_pressure_bar"] == 0.0
    assert wagons[-1]["brake_pipe_pressure_bar"] == 5.0


def test_coupler_force_analyzer():
    """Verify calculation of in-train coupler buff and draft forces during braking."""
    masses = [80.0, 50.0, 50.0, 50.0, 50.0]  # Locomotive + 4 coaches
    # Head vehicle braking hard, tail vehicle delayed
    efforts = [90.0, 70.0, 50.0, 20.0, 0.0]

    res = CouplerForceAnalyzer.compute_in_train_forces(masses, efforts, nominal_decel_ms2=1.2)
    assert res["vehicle_count"] == 5
    assert len(res["coupler_forces_kn"]) == 4
    assert res["status"] in ("SAFE", "WARNING_HIGH_BUFF")
    assert res["derailment_risk"] is False
    assert res["max_buff_compression_kn"] >= 0.0


def test_catenary_power_flow_voltage_sag():
    """Verify 25kV catenary voltage drops under heavy traction power draw."""
    network = CatenarySubstationNetwork(substation_locations_km=[0.0, 40.0])
    demands = [
        {"train_id": "EXP_1", "location_km": 20.0, "mechanical_power_kw": 4500.0, "auxiliary_power_kw": 50.0},
        {"train_id": "REG_2", "location_km": 35.0, "mechanical_power_kw": -2000.0, "auxiliary_power_kw": 30.0}
    ]

    res = network.solve_power_flow(demands)
    assert res["substation_count"] == 2
    assert res["total_grid_demand_mw"] > 0.0
    assert res["total_line_loss_mw"] > 0.0

    states = res["train_states"]
    exp_state = next(s for s in states if s["train_id"] == "EXP_1")
    # Accelerating train should experience voltage sag below 27.5 kV
    assert exp_state["pantograph_voltage_kv"] < 27.5
    assert exp_state["pantograph_voltage_kv"] >= 19.0

    # Regenerating train should show receptivity
    reg_state = next(s for s in states if s["train_id"] == "REG_2")
    assert reg_state["regenerative_receptive"] is True


def test_rolling_stock_consist_presets():
    """Verify formation specifications for HST, EMU, and Heavy Freight consists."""
    hst = RollingStockConsist.create_high_speed_consist()
    assert hst.consist_type == ConsistType.HIGH_SPEED_HST
    assert hst.total_length_m >= 180.0
    assert hst.total_power_kw >= 9000.0
    assert hst.max_operating_speed_kmh == 250.0

    freight = RollingStockConsist.create_heavy_freight_consist()
    assert freight.consist_type == ConsistType.HEAVY_HAUL_FREIGHT
    assert freight.total_mass_tons > 2500.0
    assert freight.max_tractive_effort_kn >= 800.0
    assert freight.davis_coefficients["A"] > hst.davis_coefficients["A"]


def test_physics_api_endpoints(client):
    """Test FastAPI REST endpoints for multi-physics calculations."""
    # 1. List consists
    res_consists = client.get("/physics/consists")
    assert res_consists.status_code == 200
    assert len(res_consists.json()["consists"]) == 3

    # 2. Adhesion simulation
    res_adh = client.post("/physics/simulate-adhesion", json={
        "demanded_force_kn": 250.0,
        "adhesive_mass_tons": 100.0,
        "speed_kmh": 60.0,
        "rail_condition": "LEAVES_ON_LINE",
        "wsp_enabled": True
    })
    assert res_adh.status_code == 200
    adh_data = res_adh.json()
    assert adh_data["wheel_slip_detected"] is True
    assert adh_data["sanding_recommended"] is True

    # 3. Braking simulation
    res_brake = client.post("/physics/simulate-braking", json={
        "consist_length_m": 350.0,
        "wagon_count": 14,
        "target_pipe_pressure_bar": 0.0,
        "elapsed_time_seconds": 2.0,
        "brake_mode": "PASSENGER"
    })
    assert res_brake.status_code == 200
    brake_data = res_brake.json()
    assert "coupler_analysis" in brake_data
    assert len(brake_data["wagons"]) == 14

    # 4. Catenary simulation
    res_cat = client.post("/physics/simulate-catenary", json={
        "train_demands": [
            {"train_id": "TEST_T1", "location_km": 15.0, "mechanical_power_kw": 3000.0, "auxiliary_power_kw": 40.0}
        ]
    })
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert cat_data["total_grid_demand_mw"] > 0.0
    assert len(cat_data["train_states"]) == 1
