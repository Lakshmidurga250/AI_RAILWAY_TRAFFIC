"""Tests for National Scale simulation – ZoneManager and NationalCoordinator."""

import pytest
from simulation.national_scale.zone_manager import ZoneManager, RailwayZone, IndianRailwayZone
from simulation.national_scale.national_coordinator import NationalCoordinator


# ─── ZoneManager Tests ────────────────────────────────────────────────────────

class TestZoneManager:

    @pytest.fixture
    def zm(self):
        return ZoneManager()

    def test_zone_count(self, zm):
        """Should initialise exactly 18 railway zones."""
        assert len(zm.zones) == 18

    def test_all_zone_codes_present(self, zm):
        expected = {
            "CR", "ECR", "ECoR", "ER", "NCR", "NER", "NWR",
            "NFR", "NR", "SCR", "SER", "SECR", "SWR", "SR",
            "WCR", "WR", "MR", "KR",
        }
        assert set(zm.zones.keys()) == expected

    def test_boundary_station_lookup(self, zm):
        """Known boundary stations should resolve to the correct zone."""
        assert zm.get_zone_for_station("NDLS") == "NR"
        assert zm.get_zone_for_station("MAS") == "SR"
        assert zm.get_zone_for_station("HWH") == "ER"

    def test_unknown_station_returns_none(self, zm):
        assert zm.get_zone_for_station("XXXXXX") is None

    def test_register_train_in_zone(self, zm):
        zm.register_train_in_zone("T001", "NR")
        assert "T001" in zm.zones["NR"].active_train_ids
        assert zm._train_to_zone["T001"] == "NR"

    def test_zonal_kpi_snapshot_initially_zero(self, zm):
        kpi = zm.get_zone_kpi("NR")
        assert kpi is not None
        assert kpi["zone"] == "NR"
        assert kpi["trains_running"] == 0
        assert kpi["on_time"] == 0
        assert kpi["punctuality_pct"] == 100.0

    def test_record_train_arrival_on_time(self, zm):
        zm.record_train_arrival = zm.zones["CR"].record_train_arrival  # shortcut
        zm.zones["CR"].record_train_arrival("T002", delay_minutes=2.0)
        snap = zm.zones["CR"].get_kpi_snapshot()
        assert snap.trains_on_time == 1
        assert snap.trains_delayed == 0

    def test_record_train_arrival_delayed(self, zm):
        zm.zones["SR"].record_train_arrival("T003", delay_minutes=20.0)
        snap = zm.zones["SR"].get_kpi_snapshot()
        assert snap.trains_delayed == 1
        assert snap.avg_delay_minutes == pytest.approx(20.0)

    def test_zonal_handoff_moves_train(self, zm):
        zm.register_train_in_zone("TX01", "NR")
        result = zm.process_zonal_handoff(
            train_id="TX01",
            from_zone="NR",
            to_zone="CR",
            at_station="BSL",
            delay_minutes=5.0,
            passenger_km=800.0,
            energy_kwh=2400.0,
        )
        assert result["event"] == "ZONAL_HANDOFF"
        assert result["from_zone"] == "NR"
        assert result["to_zone"] == "CR"
        # Train should now be in CR
        assert "TX01" in zm.zones["CR"].active_train_ids
        assert "TX01" not in zm.zones["NR"].active_train_ids
        # NR should have counted the handoff
        nr_snap = zm.zones["NR"].get_kpi_snapshot()
        assert nr_snap.cross_boundary_handoffs == 1

    def test_national_kpi_aggregation(self, zm):
        zm.register_train_in_zone("TA01", "NR")
        zm.register_train_in_zone("TA02", "CR")
        zm.register_train_in_zone("TA03", "WR")
        kpi = zm.get_national_kpi()
        assert kpi["national_kpi"] is True
        assert kpi["trains_running"] >= 3
        assert 0.0 <= kpi["national_punctuality_pct"] <= 100.0

    def test_alert_zones_threshold(self, zm):
        # Manually degrade NR punctuality
        for _ in range(5):
            zm.zones["NR"].record_train_arrival("X", delay_minutes=60.0)  # all delayed
        alerts = zm.get_alert_zones(punctuality_threshold=80.0)
        zone_codes = [a["zone"] for a in alerts]
        assert "NR" in zone_codes

    def test_reset_daily_metrics(self, zm):
        zm.zones["WR"].record_train_arrival("T", delay_minutes=10.0)
        zm.reset_daily_metrics()
        snap = zm.zones["WR"].get_kpi_snapshot()
        assert snap.trains_delayed == 0
        assert snap.trains_on_time == 0

    def test_get_zone_kpi_invalid(self, zm):
        assert zm.get_zone_kpi("INVALID_ZONE") is None

    def test_handoff_log_persists(self, zm):
        zm.register_train_in_zone("TH01", "ECR")
        zm.process_zonal_handoff("TH01", "ECR", "ER", "HWH")
        log = zm.get_handoff_log(limit=10)
        assert len(log) == 1
        assert log[0]["train_id"] == "TH01"


# ─── NationalCoordinator Tests ────────────────────────────────────────────────

class TestNationalCoordinator:

    @pytest.fixture
    def nc(self):
        return NationalCoordinator()

    def test_fleet_data_initialized(self, nc):
        fleet = nc.get_fleet_utilisation()
        assert len(fleet) > 0
        for rec in fleet:
            assert "fleet_type" in rec
            assert 0.0 <= rec["utilisation_pct"] <= 100.0

    def test_plan_cross_zonal_route_known_stations(self, nc):
        route = nc.plan_cross_zonal_route(
            train_id="12951",
            origin_station="NDLS",
            destination_station="BCT",
            train_type="RAJDHANI",
            estimated_distance_km=1384.0,
        )
        assert route.train_id == "12951"
        assert route.origin_zone == "NR"
        assert route.priority == "RAJDHANI"
        assert route.estimated_distance_km == pytest.approx(1384.0)
        assert isinstance(route.intermediate_zones, list)
        assert isinstance(route.boundary_handoff_stations, list)

    def test_plan_route_registers_train_in_origin_zone(self, nc):
        nc.plan_cross_zonal_route("T999", "NDLS", "MAS", "EXPRESS", 2180.0)
        assert "T999" in nc.zone_manager.zones["NR"].active_train_ids

    def test_route_stored_in_active_routes(self, nc):
        route = nc.plan_cross_zonal_route("T888", "NDLS", "MAS", "EXPRESS", 2180.0)
        assert route.route_id in nc._active_routes

    def test_get_route_status(self, nc):
        nc.plan_cross_zonal_route("T777", "NDLS", "MAS", "EXPRESS", 2180.0)
        status = nc.get_route_status("T777")
        assert status is not None
        assert status["train_id"] == "T777"
        assert status["current_zone"] == "NR"

    def test_get_route_status_unknown_train(self, nc):
        assert nc.get_route_status("NO_SUCH_TRAIN") is None

    def test_raise_alert(self, nc):
        alert = nc.raise_alert(
            alert_type="SIGNAL_FAILURE",
            zone_code="NR",
            description="Signal failure at DLI station",
            severity="CRITICAL",
            station_id="DLI",
        )
        assert alert.alert_id.startswith("NALRT_")
        assert alert.alert_type == "SIGNAL_FAILURE"
        assert alert.severity == "CRITICAL"
        assert not alert.resolved

    def test_alert_registered_in_zone_incident_count(self, nc):
        nc.raise_alert("DERAILMENT", "CR", "Minor derailment at PUNE", "HIGH")
        snap = nc.zone_manager.zones["CR"].get_kpi_snapshot()
        assert snap.incidents_today >= 1

    def test_resolve_alert(self, nc):
        alert = nc.raise_alert("FLOOD", "ECR", "Flooding near PNBE", "MEDIUM")
        success = nc.resolve_alert(alert.alert_id)
        assert success is True
        # Should not appear in active alerts
        active = nc.get_active_alerts()
        ids = [a["alert_id"] for a in active]
        assert alert.alert_id not in ids

    def test_resolve_nonexistent_alert(self, nc):
        assert nc.resolve_alert("NALRT_99999") is False

    def test_get_active_alerts_severity_filter(self, nc):
        nc.raise_alert("X", "NR", "Critical issue", "CRITICAL")
        nc.raise_alert("Y", "WR", "Medium issue", "MEDIUM")
        critical_alerts = nc.get_active_alerts(severity="CRITICAL")
        assert all(a["severity"] == "CRITICAL" for a in critical_alerts)

    def test_process_handoff_no_route_returns_none(self, nc):
        result = nc.process_handoff("GHOST_TRAIN", "NDLS")
        assert result is None

    def test_process_handoff_advances_zone(self, nc):
        """Test that process_handoff moves a train to the next zone in its route."""
        route = nc.plan_cross_zonal_route("TX55", "NDLS", "BCT", "EXPRESS", 1400.0)
        if not route.intermediate_zones:
            # Route is direct (adjacent zones) – cannot test multi-hop handoff
            pytest.skip("No intermediate zones in this corridor")
        first_boundary = route.boundary_handoff_stations[0]
        result = nc.process_handoff(
            train_id="TX55",
            at_station=first_boundary,
            delay_minutes=8.0,
            passenger_km=320.0,
            energy_kwh=960.0,
        )
        assert result is not None
        assert result["event"] == "ZONAL_HANDOFF"
        assert result["from_zone"] == route.origin_zone

    def test_ncr_dashboard_structure(self, nc):
        dash = nc.get_ncr_dashboard()
        assert dash["ncr_dashboard"] is True
        assert "national_kpi" in dash
        assert "active_alerts" in dash
        assert "fleet_utilisation" in dash
        assert "handoff_log_recent" in dash
        kpi = dash["national_kpi"]
        assert "trains_running" in kpi
        assert "national_punctuality_pct" in kpi

    def test_fleet_utilisation_update(self, nc):
        initial = next(r for r in nc.get_fleet_utilisation() if "WAP7" in r["fleet_type"])
        initial_in_service = initial["in_service"]
        nc.update_fleet_record("WAP7_ELECTRIC_LOCO", in_service_delta=-10)
        updated = next(r for r in nc.get_fleet_utilisation() if "WAP7" in r["fleet_type"])
        assert updated["in_service"] == initial_in_service - 10
