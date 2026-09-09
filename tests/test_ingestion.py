"""Tests for Data Ingestion and Quality Assurance Engine."""
import pytest
import pandas as pd
from ai.data.ingestion import DataIngestionService
from ai.data.quality import DataQualityChecker

def test_json_telemetry_ingestion():
    raw_json = '''[
        {"train_id": "TR_101", "timestamp": "2026-09-09T10:00:00Z", "speed_kmh": 120.5, "latitude": 51.5, "longitude": -0.1, "passenger_count": 350},
        {"train_id": "TR_202", "timestamp": "2026-09-09T10:00:00Z", "speed_kmh": 450.0, "latitude": 51.5, "longitude": -0.1, "passenger_count": 200}
    ]'''
    cleaned, res = DataIngestionService.ingest_telemetry_json(raw_json)
    assert res.total_rows == 2
    # 450 km/h is impossible and should be rejected
    assert res.processed_rows == 1
    assert cleaned[0]["train_id"] == "TR_101"

def test_xml_timetable_ingestion():
    xml_data = """<timetable>
      <service id="TRN_TEST_1" number="EXP-99" type="HIGH_SPEED" priority="9">
        <stop station_id="ST_CENTRAL" arrival="10:00:00" departure="10:05:00" dwell="300"/>
        <stop station_id="ST_NORTH" arrival="10:25:00" departure="10:30:00" dwell="300"/>
      </service>
    </timetable>"""
    services, res = DataIngestionService.ingest_timetable_xml(xml_data)
    assert res.processed_rows == 1
    assert services[0]["train_number"] == "EXP-99"
    assert len(services[0]["stops"]) == 2
    assert services[0]["stops"][0]["station_id"] == "ST_CENTRAL"

def test_csv_ingestion_and_cleaning():
    csv_data = """train_id,speed_kmh,delay_min
TR_101,120.0,0.0
TR_202,140.0,2.5
TR_101,120.0,0.0"""
    df, res = DataIngestionService.ingest_csv_str(csv_data)
    assert res.total_rows == 3
    assert res.processed_rows == 2  # duplicate removed
    assert "speed_kmh" in df.columns

def test_data_quality_checker_timetable():
    services = [
        {
            "train_id": "TR_1",
            "stops": [
                {"stop_sequence": 1, "station_id": "ST_CENTRAL", "dwell_seconds": 120},
                {"stop_sequence": 2, "station_id": "ST_NORTH", "dwell_seconds": 120}
            ]
        },
        {
            "train_id": "TR_2_BROKEN",
            "stops": [
                {"stop_sequence": 1, "station_id": "ST_CENTRAL", "dwell_seconds": -50}
            ]
        }
    ]
    report = DataQualityChecker.audit_timetable_batch(services)
    assert report["total_services"] == 2
    assert report["valid_services"] == 1
    assert report["status"] == "FAILED"
