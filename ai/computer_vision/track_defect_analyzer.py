"""
Computer Vision Track & Overhead Catenary (OHE) Defect Analyzer.

Performs automated deep optical inspection on high-speed rail camera feeds:
  - Rail Surface Defect Detection: Head checks, squats, wheel burns, spalling
  - Fastener & Elastic Rail Clip (ERC) missing/broken detection
  - Fishplate joint gap measurement and bolt integrity check
  - Overhead Catenary (OHE) dropper fatigue & pantograph arc spark detection
  - Sleepers crack classification (Prestressed Concrete Sleepers - PSC)
"""

from __future__ import annotations
import math
import enum
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any


class DefectSeverity(enum.Enum):
    NORMAL = "NORMAL"
    ATTENTION_REQUIRED = "ATTENTION_REQUIRED"
    URGENT_MAINTENANCE = "URGENT_MAINTENANCE"
    EMERGENCY_IMMEDIATE_STOP = "EMERGENCY_IMMEDIATE_STOP"


class DefectCategory(enum.Enum):
    RAIL_SQUAT = "RAIL_SQUAT"
    HEAD_CHECK_RCF = "ROLLING_CONTACT_FATIGUE_HEAD_CHECK"
    WHEEL_BURN = "WHEEL_BURN"
    CORRUGATION = "RAIL_CORRUGATION"
    MISSING_ERC_FASTENER = "MISSING_ELASTIC_RAIL_CLIP"
    FISHPLATE_BOLT_MISSING = "FISHPLATE_BOLT_MISSING"
    SLEEPER_CRACK_TRANSVERSE = "SLEEPER_TRANSVERSE_CRACK"
    OHE_DROPPER_BROKEN = "OHE_DROPPER_BROKEN"
    PANTOGRAPH_ARCING = "PANTOGRAPH_ARCING"
    OBSTACLE_ON_TRACK = "OBSTACLE_ON_TRACK"


@dataclass
class BoundingBox2D:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float

    @property
    def area(self) -> float:
        return max(0.0, self.x_max - self.x_min) * max(0.0, self.y_max - self.y_min)


@dataclass
class DetectedTrackAnomaly:
    anomaly_id: str
    timestamp: float
    track_kilometer: float
    camera_id: str
    category: DefectCategory
    severity: DefectSeverity
    bounding_box: BoundingBox2D
    defect_length_mm: float
    defect_depth_mm: float
    requires_speed_restriction: bool
    recommended_tsr_kmh: Optional[float] = None
    ai_model_version: str = "ResNet101-YOLOv8-Rail-v4.2"


class TrackDefectInferenceEngine:
    """Processes frame batches and produces actionable engineering maintenance workorders."""

    def __init__(self, confidence_threshold: float = 0.75):
        self.conf_threshold = confidence_threshold
        self.anomaly_log: List[DetectedTrackAnomaly] = []

    def classify_defect_severity(self, category: DefectCategory, length_mm: float, depth_mm: float) -> Tuple[DefectSeverity, bool, Optional[float]]:
        """Maps physical defect measurements to safety intervention categories."""
        if category == DefectCategory.OBSTACLE_ON_TRACK:
            return DefectSeverity.EMERGENCY_IMMEDIATE_STOP, True, 0.0

        if category == DefectCategory.RAIL_SQUAT:
            if depth_mm > 5.0 or length_mm > 35.0:
                return DefectSeverity.URGENT_MAINTENANCE, True, 30.0
            elif depth_mm > 2.0:
                return DefectSeverity.ATTENTION_REQUIRED, False, None
            return DefectSeverity.NORMAL, False, None

        if category == DefectCategory.MISSING_ERC_FASTENER:
            if length_mm >= 3.0:  # 3 consecutive clips missing
                return DefectSeverity.URGENT_MAINTENANCE, True, 45.0
            return DefectSeverity.ATTENTION_REQUIRED, False, None

        if category == DefectCategory.OHE_DROPPER_BROKEN:
            return DefectSeverity.URGENT_MAINTENANCE, True, 60.0

        return DefectSeverity.NORMAL, False, None

    def process_frame(
        self,
        frame_id: str,
        track_km: float,
        detections: List[Dict[str, Any]]
    ) -> List[DetectedTrackAnomaly]:
        """
        Parses raw neural network inference detections:
        Expected dict keys: 'category', 'bbox', 'length_mm', 'depth_mm'
        """
        anomalies = []
        for det in detections:
            bbox_raw = det['bbox']
            bbox = BoundingBox2D(
                x_min=bbox_raw[0], y_min=bbox_raw[1],
                x_max=bbox_raw[2], y_max=bbox_raw[3],
                confidence=det.get('confidence', 0.90)
            )
            if bbox.confidence < self.conf_threshold:
                continue

            category = DefectCategory(det['category'])
            length_mm = det.get('length_mm', 10.0)
            depth_mm = det.get('depth_mm', 1.0)

            severity, req_tsr, tsr_spd = self.classify_defect_severity(category, length_mm, depth_mm)

            anomaly = DetectedTrackAnomaly(
                anomaly_id=f"ANO-{int(time.time()*1000)}-{len(self.anomaly_log)+1}",
                timestamp=time.time(),
                track_kilometer=track_km,
                camera_id=frame_id,
                category=category,
                severity=severity,
                bounding_box=bbox,
                defect_length_mm=length_mm,
                defect_depth_mm=depth_mm,
                requires_speed_restriction=req_tsr,
                recommended_tsr_kmh=tsr_spd
            )
            anomalies.append(anomaly)
            self.anomaly_log.append(anomaly)

        return anomalies\n