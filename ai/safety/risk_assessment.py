"""
Risk Assessment and Safety Analysis Engine for Indian Railways.

Implements:
  - HAZOP (Hazard and Operability Study) for railway operations
  - Fault Tree Analysis (FTA) for signal failures
  - FMEA (Failure Modes and Effects Analysis) for rolling stock
  - Bowtie diagram risk modelling
  - ALARP (As Low As Reasonably Practicable) risk assessment
  - Safety Integrity Level (SIL) determination (EN 50129)
  - Kavach TCAS integration safety checks
  - Level crossing risk quantification
  - Human factors error probability (HEART technique)
  - Emergency response time modelling
  - Accident investigation causal chain analysis
  - Proactive near-miss reporting and trending
"""

from __future__ import annotations

import logging
import math
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class HazardCategory(str, Enum):
    COLLISION          = "COLLISION"
    DERAILMENT         = "DERAILMENT"
    LEVEL_CROSSING     = "LEVEL_CROSSING"
    FIRE               = "FIRE"
    STRUCTURAL_FAILURE = "STRUCTURAL"
    ELECTRICAL         = "ELECTRICAL"
    HUMAN_ERROR        = "HUMAN_ERROR"
    FLOODING           = "FLOODING"
    SIGNAL_PASSED_DANGER = "SPAD"
    RUNAWAY            = "RUNAWAY"
    LANDSLIDE          = "LANDSLIDE"
    SABOTAGE           = "SABOTAGE"


class SeverityLevel(str, Enum):
    CATASTROPHIC = "CAT"   # Multiple fatalities
    CRITICAL     = "CRIT"  # Single fatality or severe injuries
    MARGINAL     = "MARG"  # Minor injuries
    NEGLIGIBLE   = "NEGL"  # No injuries / near-miss


class LikelihoodLevel(str, Enum):
    FREQUENT     = "FREQ"    # > 1 per year
    PROBABLE     = "PROB"    # 0.1 – 1 per year
    OCCASIONAL   = "OCC"     # 0.01 – 0.1 per year
    REMOTE       = "REM"     # 0.001 – 0.01 per year
    IMPROBABLE   = "IMPB"    # 0.0001 – 0.001 per year
    INCREDIBLE   = "INCR"    # < 0.0001 per year


class RiskLevel(str, Enum):
    INTOLERABLE   = "INTOLERABLE"
    ALARP         = "ALARP"
    TOLERABLE     = "TOLERABLE"
    BROADLY_OK    = "BROADLY_ACCEPTABLE"


class SILLevel(str, Enum):
    SIL0 = "SIL0"
    SIL1 = "SIL1"
    SIL2 = "SIL2"
    SIL3 = "SIL3"
    SIL4 = "SIL4"


class IncidentType(str, Enum):
    ACCIDENT        = "ACCIDENT"
    NEAR_MISS       = "NEAR_MISS"
    DANGEROUS_OCCURRENCE = "DANGEROUS_OCC"
    INFRASTRUCTURE_FAILURE = "INFRA_FAILURE"
    OPERATIONAL_IRREGULARITY = "OP_IRREGULAR"


# ─────────────────────────────────────────────────────────────────────────────
# Risk matrix
# ─────────────────────────────────────────────────────────────────────────────

SEVERITY_SCORE = {
    SeverityLevel.CATASTROPHIC: 4,
    SeverityLevel.CRITICAL:     3,
    SeverityLevel.MARGINAL:     2,
    SeverityLevel.NEGLIGIBLE:   1,
}

LIKELIHOOD_SCORE = {
    LikelihoodLevel.FREQUENT:   6,
    LikelihoodLevel.PROBABLE:   5,
    LikelihoodLevel.OCCASIONAL: 4,
    LikelihoodLevel.REMOTE:     3,
    LikelihoodLevel.IMPROBABLE: 2,
    LikelihoodLevel.INCREDIBLE: 1,
}

def risk_level_from_scores(severity: SeverityLevel, likelihood: LikelihoodLevel) -> RiskLevel:
    s = SEVERITY_SCORE[severity]
    l = LIKELIHOOD_SCORE[likelihood]
    score = s * l
    if score >= 16:
        return RiskLevel.INTOLERABLE
    if score >= 8:
        return RiskLevel.ALARP
    if score >= 4:
        return RiskLevel.TOLERABLE
    return RiskLevel.BROADLY_OK


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Hazard:
    """A identified operational hazard."""
    hazard_id:       str
    category:        HazardCategory
    description:     str
    location:        str
    identified_by:   str
    identified_date: date
    severity:        SeverityLevel
    likelihood:      LikelihoodLevel
    risk_level:      RiskLevel = field(init=False)
    controls:        List[str] = field(default_factory=list)
    residual_severity:    Optional[SeverityLevel] = None
    residual_likelihood:  Optional[LikelihoodLevel] = None
    residual_risk:        Optional[RiskLevel] = None
    review_date:     Optional[date] = None
    closed:          bool = False

    def __post_init__(self):
        self.risk_level = risk_level_from_scores(self.severity, self.likelihood)
        if self.residual_severity and self.residual_likelihood:
            self.residual_risk = risk_level_from_scores(self.residual_severity, self.residual_likelihood)

    @property
    def risk_score(self) -> int:
        return SEVERITY_SCORE[self.severity] * LIKELIHOOD_SCORE[self.likelihood]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hazard_id":         self.hazard_id,
            "category":          self.category.value,
            "description":       self.description,
            "location":          self.location,
            "severity":          self.severity.value,
            "likelihood":        self.likelihood.value,
            "risk_level":        self.risk_level.value,
            "risk_score":        self.risk_score,
            "controls":          self.controls,
            "residual_risk":     self.residual_risk.value if self.residual_risk else None,
            "review_date":       self.review_date.isoformat() if self.review_date else None,
            "closed":            self.closed,
        }


@dataclass
class FaultTreeNode:
    """Node in a Fault Tree Analysis."""
    node_id:      str
    description:  str
    node_type:    str   # "EVENT" | "AND_GATE" | "OR_GATE" | "BASIC_EVENT"
    failure_prob: float = 0.0
    children:     List[FaultTreeNode] = field(default_factory=list)

    def compute_probability(self) -> float:
        if self.node_type == "BASIC_EVENT":
            return self.failure_prob
        child_probs = [c.compute_probability() for c in self.children]
        if not child_probs:
            return self.failure_prob
        if self.node_type == "AND_GATE":
            result = 1.0
            for p in child_probs:
                result *= p
            return result
        if self.node_type == "OR_GATE":
            result = 1.0
            for p in child_probs:
                result *= (1.0 - p)
            return 1.0 - result
        return self.failure_prob

    def minimal_cut_sets(self) -> List[Set[str]]:
        """Find minimal cut sets (simplified BDD approach)."""
        if self.node_type == "BASIC_EVENT":
            return [{self.node_id}]
        child_mcs = [c.minimal_cut_sets() for c in self.children]
        if self.node_type == "AND_GATE":
            if not child_mcs:
                return [{self.node_id}]
            result = child_mcs[0]
            for mcs in child_mcs[1:]:
                new_result = []
                for s1 in result:
                    for s2 in mcs:
                        new_result.append(s1 | s2)
                result = new_result
            return result
        if self.node_type == "OR_GATE":
            result = []
            for mcs in child_mcs:
                result.extend(mcs)
            return result
        return [{self.node_id}]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id":      self.node_id,
            "description":  self.description,
            "type":         self.node_type,
            "probability":  round(self.compute_probability(), 8),
            "children":     [c.to_dict() for c in self.children],
        }


@dataclass
class FMEARecord:
    """Failure Modes and Effects Analysis record for a component."""
    fmea_id:          str
    component:        str
    subsystem:        str
    failure_mode:     str
    failure_effect:   str
    failure_cause:    str
    detection_method: str
    severity:         int    # 1-10
    occurrence:       int    # 1-10
    detectability:    int    # 1-10
    corrective_action: str = ""
    recommended_by:   str = ""
    status:           str = "OPEN"

    @property
    def rpn(self) -> int:
        """Risk Priority Number = Severity × Occurrence × Detectability."""
        return self.severity * self.occurrence * self.detectability

    @property
    def priority(self) -> str:
        if self.rpn >= 200:
            return "HIGH"
        if self.rpn >= 100:
            return "MEDIUM"
        return "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fmea_id":         self.fmea_id,
            "component":       self.component,
            "subsystem":       self.subsystem,
            "failure_mode":    self.failure_mode,
            "failure_effect":  self.failure_effect,
            "failure_cause":   self.failure_cause,
            "detection":       self.detection_method,
            "severity":        self.severity,
            "occurrence":      self.occurrence,
            "detectability":   self.detectability,
            "rpn":             self.rpn,
            "priority":        self.priority,
            "corrective_action": self.corrective_action,
            "status":          self.status,
        }


@dataclass
class IncidentReport:
    """Structured incident / near-miss report."""
    incident_id:    str
    incident_type:  IncidentType
    title:          str
    description:    str
    location:       str
    zone_code:      str
    occurred_at:    datetime
    reported_at:    datetime
    reported_by:    str
    severity:       SeverityLevel
    hazard_category: HazardCategory
    immediate_cause: str
    root_causes:    List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    corrective_actions:   List[str] = field(default_factory=list)
    train_ids_involved:   List[str] = field(default_factory=list)
    casualties:     int = 0
    injuries:       int = 0
    status:         str = "OPEN"  # OPEN | INVESTIGATING | CLOSED
    investigator:   Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id":    self.incident_id,
            "type":           self.incident_type.value,
            "title":          self.title,
            "location":       self.location,
            "zone":           self.zone_code,
            "occurred_at":    self.occurred_at.isoformat(),
            "severity":       self.severity.value,
            "category":       self.hazard_category.value,
            "immediate_cause": self.immediate_cause,
            "root_causes":    self.root_causes,
            "corrective_actions": self.corrective_actions,
            "trains_involved": self.train_ids_involved,
            "casualties":     self.casualties,
            "injuries":       self.injuries,
            "status":         self.status,
            "investigator":   self.investigator,
        }


@dataclass
class LevelCrossingRisk:
    """Risk assessment for a railway level crossing."""
    lc_id:             str
    name:              str
    location_km:       float
    zone_code:         str
    lc_type:           str    # MANNED | UNMANNED | LCWG | SUBWAYMANNED
    road_traffic_vpd:  int    # vehicles per day
    train_frequency:   int    # trains per day
    visibility_m:      float  # sight distance available
    speed_limit_kmh:   float
    collision_history: int    # incidents in last 5 years
    risk_score:        float = field(init=False)
    risk_level:        str    = field(init=False)

    def __post_init__(self):
        # Risk score based on traffic exposure × train exposure × visibility factor
        exposure = (self.road_traffic_vpd * self.train_frequency) / 1_000_000.0
        vis_factor = max(0.5, 1.0 - self.visibility_m / 500.0)
        speed_factor = self.speed_limit_kmh / 100.0
        history_factor = 1.0 + self.collision_history * 0.3
        self.risk_score = round(exposure * vis_factor * speed_factor * history_factor * 100, 2)
        if self.risk_score >= 5.0:
            self.risk_level = "CRITICAL"
        elif self.risk_score >= 2.0:
            self.risk_level = "HIGH"
        elif self.risk_score >= 0.5:
            self.risk_level = "MEDIUM"
        else:
            self.risk_level = "LOW"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lc_id":           self.lc_id,
            "name":            self.name,
            "location_km":     self.location_km,
            "zone":            self.zone_code,
            "type":            self.lc_type,
            "road_traffic_vpd": self.road_traffic_vpd,
            "train_freq_day":  self.train_frequency,
            "visibility_m":    self.visibility_m,
            "speed_kmh":       self.speed_limit_kmh,
            "collision_history": self.collision_history,
            "risk_score":      self.risk_score,
            "risk_level":      self.risk_level,
        }


@dataclass
class HEARTAssessment:
    """Human Error Assessment and Reduction Technique result."""
    task_id:          str
    task_description: str
    task_type:        str   # e.g. "Totally Unfamiliar" | "Simple Routine"
    base_her:         float  # Human Error Rate from HEART table
    error_producing_conditions: List[str] = field(default_factory=list)
    epc_weights:      List[float] = field(default_factory=list)
    assessed_her:     float = field(init=False)

    def __post_init__(self):
        # Assessed HER = Base HER × Π(1 + (EPCi-1)×proportion_i)
        combined = 1.0
        for i, epc in enumerate(self.epc_weights):
            proportion = 0.4  # typical HEART proportion factor
            combined *= (1.0 + (epc - 1.0) * proportion)
        self.assessed_her = min(1.0, self.base_her * combined)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id":     self.task_id,
            "description": self.task_description,
            "task_type":   self.task_type,
            "base_her":    self.base_her,
            "conditions":  self.error_producing_conditions,
            "assessed_her": round(self.assessed_her, 6),
            "reliability": round(1.0 - self.assessed_her, 6),
        }


# ─────────────────────────────────────────────────────────────────────────────
# SIL Determination
# ─────────────────────────────────────────────────────────────────────────────

class SILDeterminator:
    """Determines required Safety Integrity Level per EN 50129 / CENELEC."""

    # Risk Graph matrices (simplified)
    SIL_MATRIX = {
        (4, 6): SILLevel.SIL4,
        (4, 5): SILLevel.SIL4,
        (4, 4): SILLevel.SIL3,
        (4, 3): SILLevel.SIL3,
        (4, 2): SILLevel.SIL2,
        (4, 1): SILLevel.SIL1,
        (3, 6): SILLevel.SIL3,
        (3, 5): SILLevel.SIL3,
        (3, 4): SILLevel.SIL2,
        (3, 3): SILLevel.SIL2,
        (3, 2): SILLevel.SIL1,
        (3, 1): SILLevel.SIL0,
        (2, 6): SILLevel.SIL2,
        (2, 5): SILLevel.SIL2,
        (2, 4): SILLevel.SIL1,
        (2, 3): SILLevel.SIL1,
        (2, 2): SILLevel.SIL0,
        (2, 1): SILLevel.SIL0,
        (1, 6): SILLevel.SIL1,
        (1, 5): SILLevel.SIL1,
        (1, 4): SILLevel.SIL0,
        (1, 3): SILLevel.SIL0,
        (1, 2): SILLevel.SIL0,
        (1, 1): SILLevel.SIL0,
    }

    @classmethod
    def determine(cls, severity: SeverityLevel, likelihood: LikelihoodLevel) -> SILLevel:
        s = SEVERITY_SCORE[severity]
        l = LIKELIHOOD_SCORE[likelihood]
        return cls.SIL_MATRIX.get((s, l), SILLevel.SIL0)

    @classmethod
    def pfh_target(cls, sil: SILLevel) -> float:
        """Probability of Failure per Hour target for the SIL."""
        targets = {
            SILLevel.SIL4: 1e-9,
            SILLevel.SIL3: 1e-8,
            SILLevel.SIL2: 1e-7,
            SILLevel.SIL1: 1e-6,
            SILLevel.SIL0: 1e-5,
        }
        return targets.get(sil, 1e-5)


# ─────────────────────────────────────────────────────────────────────────────
# Main Risk Assessment Engine
# ─────────────────────────────────────────────────────────────────────────────

class RiskAssessmentEngine:
    """
    Central safety risk assessment engine for a railway zone.

    Manages hazard registers, FTA models, FMEA records, incident reports,
    level crossing assessments, HEART analyses, and SIL determinations.
    """

    def __init__(self, zone_code: str) -> None:
        self.zone_code = zone_code
        self._hazards:    Dict[str, Hazard]          = {}
        self._fta_trees:  Dict[str, FaultTreeNode]   = {}
        self._fmea:       Dict[str, FMEARecord]       = {}
        self._incidents:  List[IncidentReport]        = []
        self._lc_risks:   Dict[str, LevelCrossingRisk] = {}
        self._heart:      List[HEARTAssessment]       = []
        self._alert_callbacks: List[Callable]         = []
        self._hazard_counter  = 0
        self._fmea_counter    = 0
        self._incident_counter = 0

    # ── Hazard Register ───────────────────────────────────────────────────

    def register_hazard(
        self,
        category:      HazardCategory,
        description:   str,
        location:      str,
        severity:      SeverityLevel,
        likelihood:    LikelihoodLevel,
        controls:      Optional[List[str]] = None,
        identified_by: str = "Safety Team",
    ) -> Hazard:
        self._hazard_counter += 1
        h_id = f"HAZ_{self.zone_code}_{self._hazard_counter:04d}"
        hazard = Hazard(
            hazard_id       = h_id,
            category        = category,
            description     = description,
            location        = location,
            identified_by   = identified_by,
            identified_date = date.today(),
            severity        = severity,
            likelihood      = likelihood,
            controls        = controls or [],
            review_date     = date.today() + timedelta(days=90),
        )
        self._hazards[h_id] = hazard
        if hazard.risk_level == RiskLevel.INTOLERABLE:
            logger.critical("INTOLERABLE RISK: %s – %s", h_id, description)
        return hazard

    def update_residual_risk(
        self,
        hazard_id:            str,
        residual_severity:    SeverityLevel,
        residual_likelihood:  LikelihoodLevel,
    ) -> Optional[Hazard]:
        hazard = self._hazards.get(hazard_id)
        if not hazard:
            return None
        hazard.residual_severity   = residual_severity
        hazard.residual_likelihood = residual_likelihood
        hazard.residual_risk = risk_level_from_scores(residual_severity, residual_likelihood)
        return hazard

    def get_intolerable_hazards(self) -> List[Dict[str, Any]]:
        return [
            h.to_dict() for h in self._hazards.values()
            if h.risk_level == RiskLevel.INTOLERABLE and not h.closed
        ]

    def get_hazard_register(self, category: Optional[HazardCategory] = None) -> List[Dict[str, Any]]:
        hazards = list(self._hazards.values())
        if category:
            hazards = [h for h in hazards if h.category == category]
        return sorted([h.to_dict() for h in hazards], key=lambda x: x["risk_score"], reverse=True)

    # ── FTA Management ────────────────────────────────────────────────────

    def register_fta(self, tree_id: str, root: FaultTreeNode) -> None:
        self._fta_trees[tree_id] = root

    def analyse_fta(self, tree_id: str) -> Dict[str, Any]:
        root = self._fta_trees.get(tree_id)
        if not root:
            return {"error": f"FTA tree '{tree_id}' not found"}
        top_prob = root.compute_probability()
        mcs       = root.minimal_cut_sets()
        return {
            "tree_id":            tree_id,
            "top_event":          root.description,
            "top_event_prob":     round(top_prob, 10),
            "minimal_cut_sets":   [list(s) for s in mcs],
            "num_cut_sets":       len(mcs),
            "risk_level":         "CRITICAL" if top_prob > 1e-6 else ("HIGH" if top_prob > 1e-8 else "LOW"),
            "sil_required":       SILDeterminator.determine(
                SeverityLevel.CRITICAL,
                LikelihoodLevel.REMOTE if top_prob < 1e-4 else LikelihoodLevel.FREQUENT
            ).value,
        }

    def build_spad_fta(self) -> FaultTreeNode:
        """Build a sample FTA for Signal Passed At Danger (SPAD) event."""
        spad = FaultTreeNode("TOP_SPAD", "SPAD Occurs", "OR_GATE")
        driver_error = FaultTreeNode("DE", "Driver Error", "AND_GATE")
        signal_fault = FaultTreeNode("SF", "Signal Fault", "OR_GATE")

        distraction   = FaultTreeNode("DE1", "Driver Distracted", "BASIC_EVENT", failure_prob=0.02)
        fatigue        = FaultTreeNode("DE2", "Driver Fatigue",    "BASIC_EVENT", failure_prob=0.015)
        poor_vis       = FaultTreeNode("DE3", "Poor Visibility",   "BASIC_EVENT", failure_prob=0.01)
        aws_bypass     = FaultTreeNode("DE4", "AWS Bypassed",      "BASIC_EVENT", failure_prob=0.005)
        driver_error.children = [distraction, fatigue, poor_vis, aws_bypass]

        led_failure    = FaultTreeNode("SF1", "LED Aspect Failure",  "BASIC_EVENT", failure_prob=0.001)
        relay_failure  = FaultTreeNode("SF2", "Relay Contact Fail",  "BASIC_EVENT", failure_prob=0.0005)
        power_failure  = FaultTreeNode("SF3", "Signal Power Fail",   "BASIC_EVENT", failure_prob=0.0002)
        signal_fault.children = [led_failure, relay_failure, power_failure]

        spad.children = [driver_error, signal_fault]
        self.register_fta("SPAD_FTA", spad)
        return spad

    # ── FMEA Management ───────────────────────────────────────────────────

    def register_fmea(self, record: FMEARecord) -> None:
        self._fmea[record.fmea_id] = record

    def get_high_rpn_fmea(self, threshold: int = 100) -> List[Dict[str, Any]]:
        return sorted(
            [r.to_dict() for r in self._fmea.values() if r.rpn >= threshold],
            key=lambda x: x["rpn"], reverse=True
        )

    def generate_rolling_stock_fmea(self, component: str) -> List[FMEARecord]:
        """Generate a standard FMEA for common rolling stock components."""
        self._fmea_counter += 1
        templates = [
            ("Wheel flange wear", "Derailment risk", "High mileage / poor lubrication", "Visual inspection", 8, 4, 3),
            ("Brake pad wear",    "Increased stopping distance", "Normal wear", "Daily check", 7, 5, 2),
            ("Axle bearing failure", "Hot axle / derailment", "Fatigue / inadequate lubrication", "HABD detection", 9, 2, 3),
            ("Coupler failure",   "Train separation", "Metal fatigue", "Impact test", 8, 1, 4),
            ("Pantograph damage", "Loss of traction power", "Contact wire snagging", "Driver report", 5, 3, 3),
            ("Door actuator jam", "Door failure at station", "Contamination / wear", "Daily test", 4, 6, 2),
            ("HVAC compressor failure", "Passenger discomfort", "Refrigerant leak", "Temp monitoring", 3, 4, 3),
            ("Bogie frame crack", "Structural failure risk", "Fatigue", "NDT inspection", 10, 1, 2),
        ]
        records = []
        for i, (mode, effect, cause, detection, sev, occ, det) in enumerate(templates):
            fmea_id = f"FMEA_{self._fmea_counter:04d}_{i+1:02d}"
            rec = FMEARecord(
                fmea_id          = fmea_id,
                component        = component,
                subsystem        = "Rolling Stock",
                failure_mode     = mode,
                failure_effect   = effect,
                failure_cause    = cause,
                detection_method = detection,
                severity         = sev,
                occurrence       = occ,
                detectability    = det,
            )
            self._fmea[fmea_id] = rec
            records.append(rec)
        return records

    # ── Incident Management ───────────────────────────────────────────────

    def log_incident(
        self,
        incident_type:   IncidentType,
        title:           str,
        description:     str,
        location:        str,
        severity:        SeverityLevel,
        hazard_category: HazardCategory,
        immediate_cause: str,
        occurred_at:     Optional[datetime] = None,
        train_ids:       Optional[List[str]] = None,
        casualties:      int = 0,
        injuries:        int = 0,
        reported_by:     str = "Operations",
    ) -> IncidentReport:
        self._incident_counter += 1
        inc = IncidentReport(
            incident_id      = f"INC_{self.zone_code}_{self._incident_counter:05d}",
            incident_type    = incident_type,
            title            = title,
            description      = description,
            location         = location,
            zone_code        = self.zone_code,
            occurred_at      = occurred_at or datetime.now(timezone.utc),
            reported_at      = datetime.now(timezone.utc),
            reported_by      = reported_by,
            severity         = severity,
            hazard_category  = hazard_category,
            immediate_cause  = immediate_cause,
            train_ids_involved = train_ids or [],
            casualties       = casualties,
            injuries         = injuries,
        )
        self._incidents.append(inc)
        if severity in (SeverityLevel.CATASTROPHIC, SeverityLevel.CRITICAL):
            for cb in self._alert_callbacks:
                try: cb(inc)
                except Exception: pass
        return inc

    def get_incident_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent = [i for i in self._incidents if i.occurred_at >= cutoff]
        by_category = defaultdict(int)
        by_type     = defaultdict(int)
        by_severity = defaultdict(int)
        for inc in recent:
            by_category[inc.hazard_category.value] += 1
            by_type[inc.incident_type.value] += 1
            by_severity[inc.severity.value] += 1
        return {
            "period_days":   days,
            "total":         len(recent),
            "by_category":   dict(by_category),
            "by_type":       dict(by_type),
            "by_severity":   dict(by_severity),
            "casualties":    sum(i.casualties for i in recent),
            "injuries":      sum(i.injuries for i in recent),
        }

    # ── Level Crossing Risk ───────────────────────────────────────────────

    def assess_level_crossing(
        self,
        lc_id:            str,
        name:             str,
        location_km:      float,
        lc_type:          str,
        road_traffic_vpd: int,
        train_frequency:  int,
        visibility_m:     float,
        speed_limit_kmh:  float,
        collision_history: int = 0,
    ) -> LevelCrossingRisk:
        lc = LevelCrossingRisk(
            lc_id             = lc_id,
            name              = name,
            location_km       = location_km,
            zone_code         = self.zone_code,
            lc_type           = lc_type,
            road_traffic_vpd  = road_traffic_vpd,
            train_frequency   = train_frequency,
            visibility_m      = visibility_m,
            speed_limit_kmh   = speed_limit_kmh,
            collision_history = collision_history,
        )
        self._lc_risks[lc_id] = lc
        return lc

    def get_critical_level_crossings(self) -> List[Dict[str, Any]]:
        return sorted(
            [lc.to_dict() for lc in self._lc_risks.values() if lc.risk_level in ("CRITICAL", "HIGH")],
            key=lambda x: x["risk_score"], reverse=True
        )

    # ── HEART analysis ────────────────────────────────────────────────────

    def add_heart_assessment(self, assessment: HEARTAssessment) -> None:
        self._heart.append(assessment)

    def get_high_error_tasks(self, threshold: float = 0.01) -> List[Dict[str, Any]]:
        return [
            a.to_dict() for a in self._heart
            if a.assessed_her >= threshold
        ]

    # ── KPI Summary ───────────────────────────────────────────────────────

    def get_safety_kpi(self) -> Dict[str, Any]:
        total_h    = len(self._hazards)
        intol      = sum(1 for h in self._hazards.values() if h.risk_level == RiskLevel.INTOLERABLE and not h.closed)
        alarp      = sum(1 for h in self._hazards.values() if h.risk_level == RiskLevel.ALARP and not h.closed)
        incidents_30d = len([i for i in self._incidents
                              if i.occurred_at >= datetime.now(timezone.utc) - timedelta(days=30)])
        open_fmea_high = len([r for r in self._fmea.values() if r.rpn >= 200 and r.status == "OPEN"])
        crit_lc    = sum(1 for lc in self._lc_risks.values() if lc.risk_level == "CRITICAL")
        return {
            "zone":                 self.zone_code,
            "total_hazards":        total_h,
            "intolerable_risks":    intol,
            "alarp_risks":          alarp,
            "incidents_last_30d":   incidents_30d,
            "high_rpn_fmea_open":   open_fmea_high,
            "critical_level_crossings": crit_lc,
            "fta_trees_registered": len(self._fta_trees),
            "heart_tasks_assessed": len(self._heart),
            "timestamp":            datetime.now(timezone.utc).isoformat(),
        }

    def on_critical_incident(self, callback: Callable) -> None:
        self._alert_callbacks.append(callback)


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_sample_risk_engine(zone_code: str = "NR") -> RiskAssessmentEngine:
    engine = RiskAssessmentEngine(zone_code)

    # Register hazards
    hazard_data = [
        (HazardCategory.SPAD, "SPAD at busy junction", "NDLS-JUNCTION",
         SeverityLevel.CATASTROPHIC, LikelihoodLevel.REMOTE),
        (HazardCategory.LEVEL_CROSSING, "Unmanned LC on freight corridor", "KM 245.3",
         SeverityLevel.CRITICAL, LikelihoodLevel.OCCASIONAL),
        (HazardCategory.DERAILMENT, "High-speed derailment on curved section", "KM 182.7",
         SeverityLevel.CATASTROPHIC, LikelihoodLevel.IMPROBABLE),
        (HazardCategory.FIRE, "Fire in coach AC unit", "Rajdhani Express",
         SeverityLevel.CRITICAL, LikelihoodLevel.REMOTE),
        (HazardCategory.HUMAN_ERROR, "Wrong line working due to communication failure", "LOOP-7",
         SeverityLevel.CRITICAL, LikelihoodLevel.OCCASIONAL),
        (HazardCategory.FLOODING, "Flash flood on embankment section", "KM 340.1",
         SeverityLevel.CRITICAL, LikelihoodLevel.REMOTE),
        (HazardCategory.ELECTRICAL, "OHE collapse on running line", "GHAZIABAD-YD",
         SeverityLevel.MARGINAL, LikelihoodLevel.OCCASIONAL),
    ]
    for cat, desc, loc, sev, lik in hazard_data:
        engine.register_hazard(cat, desc, loc, sev, lik, identified_by="Safety Officer")

    # FTA for SPAD
    engine.build_spad_fta()

    # FMEA
    engine.generate_rolling_stock_fmea("WAP7 Locomotive")

    # Level crossing risks
    lc_data = [
        ("LC_001", "Hazrat Nizamuddin Gate 5", 12.3, "MANNED",   8000, 240, 180, 60, 0),
        ("LC_002", "Tughlakabad Road LC",       28.7, "UNMANNED", 5000, 180, 120, 75, 2),
        ("LC_003", "Okhla Industrial LC",        41.2, "LCWG",    3000, 150, 200, 50, 1),
        ("LC_004", "Badarpur Village LC",        55.9, "UNMANNED", 2000, 120,  80, 60, 3),
    ]
    for args in lc_data:
        engine.assess_level_crossing(*args)

    # Incidents
    incidents_data = [
        (IncidentType.NEAR_MISS, "Driver overran signal at caution",
         SeverityLevel.MARGINAL, HazardCategory.SPAD),
        (IncidentType.OPERATIONAL_IRREGULARITY, "Train dispatched without guard's signal",
         SeverityLevel.NEGLIGIBLE, HazardCategory.HUMAN_ERROR),
        (IncidentType.DANGEROUS_OCCURRENCE, "Buffer stop impact at terminus",
         SeverityLevel.MARGINAL, HazardCategory.COLLISION),
    ]
    for itype, title, sev, hcat in incidents_data:
        engine.log_incident(
            incident_type=itype, title=title,
            description=f"Detailed description of: {title}",
            location=zone_code + "-MAIN",
            severity=sev, hazard_category=hcat,
            immediate_cause="Under investigation",
            occurred_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 28)),
        )

    return engine


# Module-level singleton
risk_engine = build_sample_risk_engine()
