"""
Infrastructure Health Monitor for National Railway Assets.

Continuously monitors the structural and operational health of:
  - Track geometry (gauge, alignment, cross-level, twist)
  - Bridge and viaduct structural integrity
  - Tunnel lining and groundwater ingress
  - Level crossing gates and interlocking health
  - Overhead Equipment (OHE) / catenary tension and stagger
  - Point machine health and throw force
  - Signal equipment (LED health, aspect consistency)
  - Station infrastructure (platform edge, lift/escalator)
  - Ballast condition and formation stability
  - Rail temperature and thermal stress (CWR buckling risk)

Uses:
  - Sensor-based anomaly detection
  - Trend analysis with degradation curves
  - Remaining Useful Life (RUL) prediction
  - Maintenance work order generation
  - Possessions / block planning integration
  - Risk-based prioritisation (RSSB style)
"""

from __future__ import annotations

import logging
import math
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class AssetType(str, Enum):
    TRACK          = "TRACK"
    BRIDGE         = "BRIDGE"
    TUNNEL         = "TUNNEL"
    LEVEL_CROSSING = "LEVEL_CROSSING"
    OHE            = "OHE"
    POINT_MACHINE  = "POINT_MACHINE"
    SIGNAL         = "SIGNAL"
    PLATFORM       = "PLATFORM"
    BALLAST        = "BALLAST"
    CWR            = "CWR"          # Continuously Welded Rail


class HealthGrade(str, Enum):
    A = "A"   # Excellent – no action needed
    B = "B"   # Good – routine maintenance
    C = "C"   # Fair – monitor closely
    D = "D"   # Poor – plan maintenance within 30 days
    E = "E"   # Critical – immediate action required


class MaintenanceType(str, Enum):
    CORRECTIVE    = "CORRECTIVE"
    PREVENTIVE    = "PREVENTIVE"
    PREDICTIVE    = "PREDICTIVE"
    CONDITION_BASED = "CBM"


class PossessionType(str, Enum):
    BLOCK           = "BLOCK"      # full block possession
    CAUTION_ORDER   = "CAUTION"    # reduced speed order
    ENGINEERING_RUN = "ENG_RUN"    # engineering train movement


# ─────────────────────────────────────────────────────────────────────────────
# Sensor reading and threshold definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SensorReading:
    """A single reading from an infrastructure sensor."""
    sensor_id:    str
    asset_id:     str
    asset_type:   AssetType
    parameter:    str        # e.g. "gauge_mm", "temp_celsius", "vibration_g"
    value:        float
    unit:         str
    timestamp:    datetime
    latitude:     Optional[float] = None
    longitude:    Optional[float] = None
    raw_signal:   Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_id":  self.sensor_id,
            "asset_id":   self.asset_id,
            "asset_type": self.asset_type.value,
            "parameter":  self.parameter,
            "value":      round(self.value, 4),
            "unit":       self.unit,
            "timestamp":  self.timestamp.isoformat(),
        }


TRACK_THRESHOLDS = {
    "gauge_mm":         {"nominal": 1676, "warn": 1680, "critical": 1685},   # broad gauge
    "cross_level_mm":   {"nominal": 0,    "warn":    8, "critical":   15},
    "twist_mm_per_m":   {"nominal": 0,    "warn":    2, "critical":    4},
    "alignment_mm":     {"nominal": 0,    "warn":    8, "critical":   15},
    "unevenness_mm":    {"nominal": 0,    "warn":    8, "critical":   13},
    "wear_mm":          {"nominal": 0,    "warn":    8, "critical":   13},   # vertical rail head wear
    "surface_defect":   {"nominal": 0,    "warn":    1, "critical":    3},   # defects per km
}

OHE_THRESHOLDS = {
    "contact_wire_height_mm": {"nominal": 5500, "warn_low": 5350, "warn_high": 5750, "critical_low": 5300},
    "stagger_mm":             {"nominal": 200,  "warn": 250, "critical": 300},
    "tension_kn":             {"nominal": 15.0, "warn_low": 13.0, "critical_low": 11.0},
    "wear_pct":               {"nominal": 0,    "warn": 70, "critical": 85},
}

RAIL_TEMP_THRESHOLDS = {
    "stress_free_temp_c": 35.0,    # rail neutral temperature (Indian Railways typical)
    "buckle_risk_temp_c": 65.0,    # CWR buckling risk threshold
    "low_risk_temp_c":    -5.0,    # fracture risk in cold weather
}


# ─────────────────────────────────────────────────────────────────────────────
# Asset data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class InfraAsset:
    """Base class for a monitored infrastructure asset."""
    asset_id:       str
    asset_type:     AssetType
    name:           str
    zone_code:      str
    division:       str
    location_km:    float           # km from section origin
    installed_date: date
    last_inspected: Optional[date]  = None
    health_grade:   HealthGrade     = HealthGrade.A
    rul_days:       Optional[int]   = None   # remaining useful life
    notes:          str             = ""

    @property
    def age_years(self) -> float:
        return (date.today() - self.installed_date).days / 365.25

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id":       self.asset_id,
            "type":           self.asset_type.value,
            "name":           self.name,
            "zone":           self.zone_code,
            "division":       self.division,
            "location_km":    self.location_km,
            "age_years":      round(self.age_years, 1),
            "last_inspected": self.last_inspected.isoformat() if self.last_inspected else None,
            "health_grade":   self.health_grade.value,
            "rul_days":       self.rul_days,
            "notes":          self.notes,
        }


@dataclass
class TrackSection(InfraAsset):
    """A discrete track section with geometry parameters."""
    length_km:         float = 1.0
    track_class:       str   = "A"    # A/B/C/D/E (Indian Railways classification)
    rail_section:      str   = "52kg" # 52kg / 60kg / 90R
    max_speed_kmh:     float = 110.0
    curvature_degrees: float = 0.0
    gradient_pct:      float = 0.0
    mgt_billion:       float = 0.0   # million gross tonnes cumulative traffic

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update({
            "length_km":         self.length_km,
            "track_class":       self.track_class,
            "rail_section":      self.rail_section,
            "max_speed_kmh":     self.max_speed_kmh,
            "curvature_degrees": self.curvature_degrees,
            "gradient_pct":      self.gradient_pct,
            "mgt_billion":       round(self.mgt_billion, 3),
        })
        return d


@dataclass
class MaintenanceWorkOrder:
    """A generated maintenance work order."""
    wo_id:            str
    asset_id:         str
    asset_type:       AssetType
    maintenance_type: MaintenanceType
    priority:         str             # P1/P2/P3/P4
    description:      str
    location_km:      float
    zone_code:        str
    raised_at:        datetime
    due_by:           datetime
    estimated_hours:  float
    crew_required:    int
    possession_needed: bool = False
    possession_type:  Optional[PossessionType] = None
    status:           str = "OPEN"    # OPEN | IN_PROGRESS | COMPLETED | DEFERRED
    completed_at:     Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wo_id":             self.wo_id,
            "asset_id":          self.asset_id,
            "type":              self.asset_type.value,
            "maintenance_type":  self.maintenance_type.value,
            "priority":          self.priority,
            "description":       self.description,
            "location_km":       self.location_km,
            "zone":              self.zone_code,
            "raised_at":         self.raised_at.isoformat(),
            "due_by":            self.due_by.isoformat(),
            "estimated_hours":   self.estimated_hours,
            "crew_required":     self.crew_required,
            "possession_needed": self.possession_needed,
            "possession_type":   self.possession_type.value if self.possession_type else None,
            "status":            self.status,
            "completed_at":      self.completed_at.isoformat() if self.completed_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# RUL Predictor
# ─────────────────────────────────────────────────────────────────────────────

class RULPredictor:
    """
    Remaining Useful Life predictor using simplified degradation models.

    Models:
    - Track geometry degradation: linear with MGT accumulation + periodic tamping
    - OHE contact wire: linear wear model (mm/year based on traffic density)
    - Point machine: Weibull failure model based on operation count
    - Rail temperature stress: thermal fatigue cycle model
    """

    @staticmethod
    def predict_track_rul(asset: TrackSection, sensor_readings: List[SensorReading]) -> int:
        """Predict remaining days before track needs major maintenance."""
        # Use gauge deviation as primary indicator
        latest_gauge = next(
            (r.value for r in reversed(sensor_readings)
             if r.asset_id == asset.asset_id and r.parameter == "gauge_mm"),
            TRACK_THRESHOLDS["gauge_mm"]["nominal"]
        )
        deviation = abs(latest_gauge - TRACK_THRESHOLDS["gauge_mm"]["nominal"])
        critical_dev = TRACK_THRESHOLDS["gauge_mm"]["critical"] - TRACK_THRESHOLDS["gauge_mm"]["nominal"]
        warn_dev     = TRACK_THRESHOLDS["gauge_mm"]["warn"] - TRACK_THRESHOLDS["gauge_mm"]["nominal"]

        # Degradation rate: assume linear with MGT
        mgt_rate = max(0.1, asset.mgt_billion)
        daily_degradation = (mgt_rate * 0.001)   # mm/day (simplified)

        if daily_degradation <= 0:
            return 365 * 5

        remaining_mm = critical_dev - deviation
        if remaining_mm <= 0:
            return 0
        rul = int(remaining_mm / daily_degradation)
        return max(0, min(rul, 365 * 10))

    @staticmethod
    def predict_ohe_rul(contact_wire_wear_pct: float, wear_rate_pct_per_year: float = 8.0) -> int:
        """Predict days to OHE contact wire renewal."""
        remaining_pct = max(0, 100.0 - contact_wire_wear_pct)
        if wear_rate_pct_per_year <= 0:
            return 365 * 15
        rul_years = remaining_pct / wear_rate_pct_per_year
        return max(0, int(rul_years * 365))

    @staticmethod
    def predict_point_machine_rul(operation_count: int, max_operations: int = 500_000) -> int:
        """Weibull-based remaining life for a point machine."""
        k = 2.5       # shape parameter
        lambda_ = max_operations
        remaining_ops = max(0, max_operations - operation_count)
        daily_ops = 120  # typical operations per day
        rul_days = int(remaining_ops / max(daily_ops, 1))
        return max(0, rul_days)

    @staticmethod
    def cwr_buckling_risk(
        rail_temp_c: float,
        stress_free_temp: float = RAIL_TEMP_THRESHOLDS["stress_free_temp_c"],
        section: str = "60kg",
    ) -> Dict[str, Any]:
        """Assess CWR buckling risk based on current rail temperature."""
        delta_t = rail_temp_c - stress_free_temp
        # Thermal stress: E × α × ΔT (MPa)
        # E_steel = 210 GPa, α = 12×10⁻⁶ /°C
        thermal_stress_mpa = 210_000 * 12e-6 * delta_t / 1000.0
        buckling_threshold_mpa = 120.0   # typical for broad gauge CWR
        risk_pct = min(100.0, max(0.0, thermal_stress_mpa / buckling_threshold_mpa * 100.0))

        return {
            "rail_temp_c":          round(rail_temp_c, 1),
            "stress_free_temp_c":   stress_free_temp,
            "delta_t":              round(delta_t, 1),
            "thermal_stress_mpa":   round(thermal_stress_mpa, 1),
            "buckling_risk_pct":    round(risk_pct, 1),
            "risk_level":           (
                "CRITICAL" if risk_pct >= 80 else
                "HIGH"     if risk_pct >= 60 else
                "MEDIUM"   if risk_pct >= 40 else
                "LOW"
            ),
            "action_required":      risk_pct >= 60,
            "speed_restriction_kmh": (10 if risk_pct >= 80 else 30 if risk_pct >= 60 else None),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Work Order Generator
# ─────────────────────────────────────────────────────────────────────────────

class WorkOrderGenerator:
    """Generates maintenance work orders from health assessments."""

    PRIORITY_MATRIX = {
        HealthGrade.E: ("P1", 1,  "IMMEDIATE"),
        HealthGrade.D: ("P2", 7,  "URGENT"),
        HealthGrade.C: ("P3", 30, "ROUTINE"),
        HealthGrade.B: ("P4", 90, "PLANNED"),
        HealthGrade.A: ("P4", 180,"PLANNED"),
    }

    ESTIMATED_HOURS = {
        AssetType.TRACK:          8.0,
        AssetType.BRIDGE:        24.0,
        AssetType.TUNNEL:        16.0,
        AssetType.LEVEL_CROSSING: 4.0,
        AssetType.OHE:            6.0,
        AssetType.POINT_MACHINE:  3.0,
        AssetType.SIGNAL:         2.0,
        AssetType.PLATFORM:       8.0,
        AssetType.BALLAST:       12.0,
        AssetType.CWR:            6.0,
    }

    CREW_REQUIREMENTS = {
        AssetType.TRACK:          8,
        AssetType.BRIDGE:        12,
        AssetType.TUNNEL:        10,
        AssetType.LEVEL_CROSSING: 4,
        AssetType.OHE:            4,
        AssetType.POINT_MACHINE:  2,
        AssetType.SIGNAL:         2,
        AssetType.PLATFORM:       6,
        AssetType.BALLAST:       10,
        AssetType.CWR:            4,
    }

    def __init__(self) -> None:
        self._counter = 0

    def _new_wo_id(self) -> str:
        self._counter += 1
        return f"WO_{self._counter:07d}"

    def generate(self, asset: InfraAsset, description: str,
                 maintenance_type: MaintenanceType = MaintenanceType.PREDICTIVE) -> MaintenanceWorkOrder:
        priority_code, due_days, _ = self.PRIORITY_MATRIX.get(asset.health_grade,
                                                               ("P4", 180, "PLANNED"))
        now    = datetime.now(timezone.utc)
        due_by = now + timedelta(days=due_days)
        poss_needed = asset.asset_type in (AssetType.TRACK, AssetType.BRIDGE,
                                           AssetType.OHE, AssetType.CWR)
        poss_type = PossessionType.BLOCK if poss_needed and asset.health_grade == HealthGrade.E else (
            PossessionType.CAUTION_ORDER if poss_needed else None
        )
        return MaintenanceWorkOrder(
            wo_id             = self._new_wo_id(),
            asset_id          = asset.asset_id,
            asset_type        = asset.asset_type,
            maintenance_type  = maintenance_type,
            priority          = priority_code,
            description       = description,
            location_km       = asset.location_km,
            zone_code         = asset.zone_code,
            raised_at         = now,
            due_by            = due_by,
            estimated_hours   = self.ESTIMATED_HOURS.get(asset.asset_type, 4.0),
            crew_required     = self.CREW_REQUIREMENTS.get(asset.asset_type, 4),
            possession_needed = poss_needed,
            possession_type   = poss_type,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Infrastructure Health Monitor — main class
# ─────────────────────────────────────────────────────────────────────────────

class InfrastructureHealthMonitor:
    """
    Central monitor for all national railway infrastructure assets.

    Responsibilities:
    - Ingest sensor readings from track recording cars, IoT sensors, manual inspections
    - Compute health grades and detect anomalies
    - Predict RUL for each asset
    - Generate and prioritise maintenance work orders
    - Produce operational risk heatmaps
    - Manage possession / block schedule integration
    """

    def __init__(self) -> None:
        self._assets:    Dict[str, InfraAsset]          = {}
        self._readings:  List[SensorReading]             = []
        self._work_orders: List[MaintenanceWorkOrder]    = []
        self._rul_predictor   = RULPredictor()
        self._wo_generator    = WorkOrderGenerator()
        self._anomaly_callbacks: List[Callable] = []

    # ── Asset registration ────────────────────────────────────────────────

    def register_asset(self, asset: InfraAsset) -> None:
        self._assets[asset.asset_id] = asset
        logger.debug("Asset registered: %s (%s)", asset.asset_id, asset.asset_type.value)

    def get_asset(self, asset_id: str) -> Optional[InfraAsset]:
        return self._assets.get(asset_id)

    # ── Sensor ingestion ──────────────────────────────────────────────────

    def ingest_reading(self, reading: SensorReading) -> List[Dict[str, Any]]:
        """Ingest a sensor reading and return any anomaly alerts generated."""
        self._readings.append(reading)
        return self._assess_reading(reading)

    def ingest_batch(self, readings: List[SensorReading]) -> List[Dict[str, Any]]:
        all_alerts: List[Dict[str, Any]] = []
        for r in readings:
            all_alerts.extend(self.ingest_reading(r))
        return all_alerts

    def _assess_reading(self, reading: SensorReading) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        asset = self._assets.get(reading.asset_id)
        if not asset:
            return alerts

        # Track geometry checks
        if reading.asset_type == AssetType.TRACK and reading.parameter in TRACK_THRESHOLDS:
            thres = TRACK_THRESHOLDS[reading.parameter]
            if reading.value > thres["critical"]:
                grade = HealthGrade.E
                sev   = "CRITICAL"
                wo    = self._wo_generator.generate(
                    asset,
                    f"Critical {reading.parameter} ({reading.value:.1f}{reading.unit}) "
                    f"exceeds threshold {thres['critical']}",
                    MaintenanceType.CORRECTIVE
                )
                self._work_orders.append(wo)
                alerts.append(self._build_alert(reading, sev, wo.wo_id))
            elif reading.value > thres["warn"]:
                grade = HealthGrade.D
                sev   = "WARNING"
                alerts.append(self._build_alert(reading, sev))
            else:
                grade = HealthGrade.A

            if grade.value < asset.health_grade.value:
                asset.health_grade = grade

        # OHE checks
        if reading.asset_type == AssetType.OHE:
            if reading.parameter == "wear_pct" and reading.value > OHE_THRESHOLDS["wear_pct"]["critical"]:
                asset.health_grade = HealthGrade.E
                wo = self._wo_generator.generate(
                    asset,
                    f"OHE contact wire wear {reading.value:.0f}% — renewal required",
                    MaintenanceType.CORRECTIVE
                )
                self._work_orders.append(wo)
                alerts.append(self._build_alert(reading, "CRITICAL", wo.wo_id))

        # CWR temperature check
        if reading.asset_type == AssetType.CWR and reading.parameter == "rail_temp_c":
            risk = RULPredictor.cwr_buckling_risk(reading.value)
            if risk["action_required"]:
                asset.health_grade = HealthGrade.D if risk["risk_level"] == "HIGH" else HealthGrade.E
                alerts.append({
                    "alert_type": "CWR_BUCKLING_RISK",
                    "asset_id":   reading.asset_id,
                    "severity":   risk["risk_level"],
                    "detail":     risk,
                    "timestamp":  reading.timestamp.isoformat(),
                })

        for cb in self._anomaly_callbacks:
            try:
                cb(reading, alerts)
            except Exception:
                pass

        return alerts

    def _build_alert(self, reading: SensorReading, severity: str,
                     wo_id: Optional[str] = None) -> Dict[str, Any]:
        return {
            "alert_type": f"{reading.asset_type.value}_ANOMALY",
            "asset_id":   reading.asset_id,
            "parameter":  reading.parameter,
            "value":      round(reading.value, 3),
            "unit":       reading.unit,
            "severity":   severity,
            "wo_id":      wo_id,
            "timestamp":  reading.timestamp.isoformat(),
        }

    # ── Health assessment ─────────────────────────────────────────────────

    def run_health_sweep(self) -> Dict[str, Any]:
        """Re-assess health grades and RUL for all assets."""
        updated  = 0
        wo_raised = 0

        for asset_id, asset in self._assets.items():
            asset_readings = [r for r in self._readings[-5000:] if r.asset_id == asset_id]

            # Update RUL
            if isinstance(asset, TrackSection):
                asset.rul_days = RULPredictor.predict_track_rul(asset, asset_readings)
                # Degrade health grade if RUL is short
                if asset.rul_days is not None:
                    if asset.rul_days <= 7:
                        asset.health_grade = HealthGrade.E
                    elif asset.rul_days <= 30:
                        asset.health_grade = min(asset.health_grade, HealthGrade.D,
                                                 key=lambda g: list(HealthGrade).index(g))

            # Auto-generate preventive WO if grade is C or worse and no open WO
            open_wo_ids = {wo.asset_id for wo in self._work_orders if wo.status == "OPEN"}
            if asset.health_grade in (HealthGrade.C, HealthGrade.D, HealthGrade.E) \
                    and asset_id not in open_wo_ids:
                wo = self._wo_generator.generate(
                    asset,
                    f"Preventive maintenance triggered by health grade {asset.health_grade.value}",
                    MaintenanceType.PREDICTIVE,
                )
                self._work_orders.append(wo)
                wo_raised += 1

            asset.last_inspected = date.today()
            updated += 1

        return {
            "assets_assessed": updated,
            "work_orders_raised": wo_raised,
            "total_open_wo": sum(1 for w in self._work_orders if w.status == "OPEN"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # ── Reporting ─────────────────────────────────────────────────────────

    def get_asset_health_report(self, zone_code: Optional[str] = None) -> List[Dict[str, Any]]:
        assets = self._assets.values()
        if zone_code:
            assets = [a for a in assets if a.zone_code == zone_code]
        return sorted([a.to_dict() for a in assets],
                      key=lambda x: ["A","B","C","D","E"].index(x.get("health_grade","A")),
                      reverse=True)

    def get_work_orders(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        wos = self._work_orders
        if status:
            wos = [w for w in wos if w.status == status]
        if priority:
            wos = [w for w in wos if w.priority == priority]
        return [w.to_dict() for w in sorted(wos, key=lambda w: w.raised_at, reverse=True)[:limit]]

    def get_risk_heatmap(self) -> List[Dict[str, Any]]:
        """Return assets sorted by risk score (grade × age × asset type weight)."""
        type_weights = {
            AssetType.BRIDGE: 5, AssetType.TUNNEL: 5, AssetType.TRACK: 3,
            AssetType.OHE: 3, AssetType.CWR: 4, AssetType.POINT_MACHINE: 2,
            AssetType.SIGNAL: 2, AssetType.LEVEL_CROSSING: 3,
            AssetType.PLATFORM: 1, AssetType.BALLAST: 2,
        }
        grade_scores = {"A": 0, "B": 1, "C": 2, "D": 4, "E": 8}
        heatmap = []
        for a in self._assets.values():
            g_score = grade_scores.get(a.health_grade.value, 0)
            t_weight = type_weights.get(a.asset_type, 1)
            age_factor = min(3.0, a.age_years / 20.0)
            risk_score = g_score * t_weight * (1 + age_factor)
            heatmap.append({
                **a.to_dict(),
                "risk_score": round(risk_score, 2),
                "risk_level": "CRITICAL" if risk_score >= 20 else
                               "HIGH"    if risk_score >= 10 else
                               "MEDIUM"  if risk_score >= 5  else "LOW",
            })
        return sorted(heatmap, key=lambda x: x["risk_score"], reverse=True)

    def get_possession_schedule(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Return required possessions for open P1/P2 work orders in the next N days."""
        now    = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        return [
            w.to_dict() for w in self._work_orders
            if w.possession_needed
            and w.status == "OPEN"
            and w.due_by <= cutoff
        ]

    def get_kpi_summary(self) -> Dict[str, Any]:
        total  = len(self._assets)
        grades = defaultdict(int)
        for a in self._assets.values():
            grades[a.health_grade.value] += 1
        open_p1 = sum(1 for w in self._work_orders if w.status == "OPEN" and w.priority == "P1")
        return {
            "total_assets":     total,
            "grade_breakdown":  dict(grades),
            "assets_critical":  grades.get("E", 0),
            "assets_poor":      grades.get("D", 0),
            "open_work_orders": sum(1 for w in self._work_orders if w.status == "OPEN"),
            "open_p1_urgent":   open_p1,
            "sensor_readings":  len(self._readings),
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }

    def on_anomaly(self, callback: Callable) -> None:
        self._anomaly_callbacks.append(callback)

    def complete_work_order(self, wo_id: str) -> bool:
        for wo in self._work_orders:
            if wo.wo_id == wo_id and wo.status in ("OPEN", "IN_PROGRESS"):
                wo.status       = "COMPLETED"
                wo.completed_at = datetime.now(timezone.utc)
                asset = self._assets.get(wo.asset_id)
                if asset:
                    asset.health_grade = HealthGrade.B   # post-maintenance improvement
                    asset.last_inspected = date.today()
                return True
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_sample_monitor() -> InfrastructureHealthMonitor:
    """Build a sample IHM pre-loaded with realistic Indian Railway assets."""
    ihm = InfrastructureHealthMonitor()
    zones = ["NR", "CR", "WR", "SR", "SCR", "ER"]
    asset_types_dist = [
        (AssetType.TRACK, 0.35),
        (AssetType.BRIDGE, 0.10),
        (AssetType.OHE, 0.15),
        (AssetType.POINT_MACHINE, 0.15),
        (AssetType.SIGNAL, 0.10),
        (AssetType.CWR, 0.08),
        (AssetType.BALLAST, 0.05),
        (AssetType.TUNNEL, 0.02),
    ]

    for i in range(200):
        atype = random.choices(
            [t for t, _ in asset_types_dist],
            weights=[w for _, w in asset_types_dist]
        )[0]
        zone = random.choice(zones)
        installed = date.today() - timedelta(days=random.randint(365, 365 * 30))
        grade_choices = list(HealthGrade)
        grade = random.choices(grade_choices, weights=[0.35, 0.30, 0.20, 0.10, 0.05])[0]

        if atype == AssetType.TRACK:
            asset = TrackSection(
                asset_id       = f"TRK_{i+1:04d}",
                asset_type     = AssetType.TRACK,
                name           = f"Track Section {zone}-{i+1}",
                zone_code      = zone,
                division       = f"{zone}-DIV{random.randint(1,4)}",
                location_km    = round(random.uniform(0, 500), 2),
                installed_date = installed,
                health_grade   = grade,
                rul_days       = random.randint(30, 365 * 5),
                length_km      = round(random.uniform(0.5, 10.0), 2),
                max_speed_kmh  = random.choice([75, 100, 110, 130, 160]),
                mgt_billion    = round(random.uniform(0.1, 8.0), 2),
            )
        else:
            asset = InfraAsset(
                asset_id       = f"{atype.value[:3]}_{i+1:04d}",
                asset_type     = atype,
                name           = f"{atype.value.title()} {zone}-{i+1}",
                zone_code      = zone,
                division       = f"{zone}-DIV{random.randint(1,4)}",
                location_km    = round(random.uniform(0, 500), 2),
                installed_date = installed,
                health_grade   = grade,
                rul_days       = random.randint(10, 365 * 8),
            )

        ihm.register_asset(asset)

        # Generate some sensor readings
        for _ in range(random.randint(3, 10)):
            if atype == AssetType.TRACK:
                param = random.choice(list(TRACK_THRESHOLDS.keys()))
                nominal = TRACK_THRESHOLDS[param]["nominal"]
                noise   = random.gauss(0, 3)
                value   = nominal + noise
            elif atype == AssetType.CWR:
                param   = "rail_temp_c"
                value   = random.uniform(20, 72)
            elif atype == AssetType.OHE:
                param   = "wear_pct"
                value   = random.uniform(20, 95)
            else:
                param   = "health_score"
                value   = random.uniform(50, 100)

            reading = SensorReading(
                sensor_id  = f"SEN_{random.randint(1000,9999)}",
                asset_id   = asset.asset_id,
                asset_type = atype,
                parameter  = param,
                value      = round(value, 3),
                unit       = "mm" if "mm" in param else ("%" if "pct" in param else "°C" if "temp" in param else "score"),
                timestamp  = datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 1440)),
            )
            ihm._readings.append(reading)

    logger.info("Sample IHM built: %d assets, %d readings", len(ihm._assets), len(ihm._readings))
    return ihm


# Module-level singleton
infrastructure_monitor = build_sample_monitor()
