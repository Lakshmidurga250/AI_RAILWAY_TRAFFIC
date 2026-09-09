"""Railway Data Quality Checker and Assurance Engine."""
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime

class DataQualityChecker:
    """Validates operational and telemetry data integrity and generates DQ reports."""

    @classmethod
    def audit_telemetry_batch(cls, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit a list of train telemetry or timetable records."""
        total_records = len(records)
        if total_records == 0:
            return {"score": 100.0, "status": "PASSED", "issues": [], "rejected_count": 0}

        issues = []
        rejected = []
        valid_count = 0

        for idx, rec in enumerate(records):
            rec_issues = []
            
            # Check mandatory fields
            for field in ["train_id", "timestamp"]:
                if field not in rec or rec[field] is None:
                    rec_issues.append(f"Missing mandatory field '{field}'")

            # Check impossible speeds
            speed = rec.get("speed_kmh")
            if speed is not None:
                if not isinstance(speed, (int, float)) or speed < 0.0 or speed > 380.0:
                    rec_issues.append(f"Impossible speed value: {speed} km/h (valid: 0-380)")

            # Check coordinates
            lat = rec.get("latitude")
            lng = rec.get("longitude")
            if lat is not None and (lat < -90.0 or lat > 90.0):
                rec_issues.append(f"Invalid latitude: {lat}")
            if lng is not None and (lng < -180.0 or lng > 180.0):
                rec_issues.append(f"Invalid longitude: {lng}")

            # Check passenger count
            pax = rec.get("passenger_count")
            if pax is not None and (pax < 0 or pax > 2500):
                rec_issues.append(f"Unrealistic passenger count: {pax}")

            if rec_issues:
                rejected.append({"index": idx, "record": rec, "reasons": rec_issues})
                issues.extend(rec_issues)
            else:
                valid_count += 1

        score = round((valid_count / total_records) * 100.0, 2)
        status = "PASSED" if score >= 95.0 else ("WARNING" if score >= 80.0 else "FAILED")

        return {
            "total_records": total_records,
            "valid_records": valid_count,
            "rejected_count": len(rejected),
            "score": score,
            "status": status,
            "issues_sample": issues[:10],
            "rejected_records": rejected[:5]
        }
