import json
import io
import xml.etree.ElementTree as ET
import pandas as pd
from typing import List, Dict, Any, Union, Tuple, Optional
from datetime import datetime, timezone
from ai.data.quality import DataQualityChecker

class IngestionResult:
    def __init__(self, total_rows: int, processed_rows: int, rejected_rows: int, dq_score: float, errors: List[str]):
        self.total_rows = total_rows
        self.processed_rows = processed_rows
        self.rejected_rows = rejected_rows
        self.dq_score = dq_score
        self.errors = errors
        self.ingested_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "rejected_rows": self.rejected_rows,
            "dq_score": self.dq_score,
            "errors": self.errors,
            "ingested_at": self.ingested_at.isoformat()
        }

class DataIngestionService:
    """Ingests and cleans external railway timetable and sensor telemetry data."""

    @classmethod
    def ingest_telemetry_json(cls, raw_json_str: str) -> Tuple[List[Dict[str, Any]], IngestionResult]:
        try:
            records = json.loads(raw_json_str)
            if isinstance(records, dict):
                records = [records]
        except Exception as e:
            res = IngestionResult(0, 0, 0, 0.0, [f"JSON Parse Error: {str(e)}"])
            return [], res

        audit = DataQualityChecker.audit_telemetry_batch(records)
        cleaned = []
        for r in records:
            # Impute missing values
            speed = float(r.get("speed_kmh", 0.0))
            if speed < 0 or speed > 380:
                continue
            cleaned.append({
                "train_id": str(r.get("train_id")),
                "timestamp": r.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "speed_kmh": speed,
                "latitude": float(r.get("latitude", 0.0)),
                "longitude": float(r.get("longitude", 0.0)),
                "current_track_id": r.get("current_track_id"),
                "power_draw_kw": float(r.get("power_draw_kw", 0.0)),
                "current_delay_min": max(0.0, float(r.get("current_delay_min", 0.0))),
                "passenger_count": int(r.get("passenger_count", 0))
            })

        result = IngestionResult(
            total_rows=len(records),
            processed_rows=len(cleaned),
            rejected_rows=len(records) - len(cleaned),
            dq_score=audit["score"],
            errors=audit["issues_sample"]
        )
        return cleaned, result

    @classmethod
    def ingest_csv_dataframe(cls, df: pd.DataFrame) -> Tuple[pd.DataFrame, IngestionResult]:
        initial_len = len(df)
        # Drop strict duplicates
        cleaned_df = df.drop_duplicates()
        
        # Fill missing numeric values with median
        num_cols = cleaned_df.select_dtypes(include=['number']).columns
        cleaned_df[num_cols] = cleaned_df[num_cols].fillna(cleaned_df[num_cols].median())
        
        # Outlier clipping on speeds if present
        if "speed_kmh" in cleaned_df.columns:
            cleaned_df["speed_kmh"] = cleaned_df["speed_kmh"].clip(0.0, 380.0)

        result = IngestionResult(
            total_rows=initial_len,
            processed_rows=len(cleaned_df),
            rejected_rows=initial_len - len(cleaned_df),
            dq_score=round((len(cleaned_df) / max(1, initial_len)) * 100.0, 2),
            errors=[]
        )
        return cleaned_df, result

    @classmethod
    def ingest_timetable_xml(cls, xml_content: str) -> Tuple[List[Dict[str, Any]], IngestionResult]:
        """Parse and validate XML formatted railway timetable schedules."""
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            res = IngestionResult(0, 0, 0, 0.0, [f"XML Syntax Error: {str(e)}"])
            return [], res

        services = []
        errors = []
        total_items = 0

        # Support both <timetable><service> and <railml><trainSchedule> structures
        train_elements = root.findall(".//service") or root.findall(".//train") or root.findall(".//trainSchedule")
        total_items = len(train_elements)

        for elem in train_elements:
            train_id = elem.get("id") or elem.findtext("id") or elem.findtext("train_id")
            train_num = elem.get("number") or elem.findtext("number") or elem.findtext("train_number") or train_id
            train_type = elem.get("type") or elem.findtext("type") or "INTERCITY"
            prio_str = elem.get("priority") or elem.findtext("priority") or "5"
            try:
                priority = int(prio_str)
            except ValueError:
                priority = 5

            stops = []
            stop_nodes = elem.findall(".//stop") or elem.findall(".//station")
            for idx, st in enumerate(stop_nodes, start=1):
                stn_id = st.get("station_id") or st.get("id") or st.text
                arr = st.get("arrival") or st.get("scheduled_arrival")
                dep = st.get("departure") or st.get("scheduled_departure")
                platform = st.get("platform") or f"{stn_id}_P1"
                dwell_str = st.get("dwell") or "120"
                try:
                    dwell = int(dwell_str)
                except ValueError:
                    dwell = 120

                if stn_id:
                    stops.append({
                        "stop_sequence": idx,
                        "station_id": stn_id,
                        "platform_id": platform,
                        "scheduled_arrival": arr,
                        "scheduled_departure": dep,
                        "dwell_seconds": dwell
                    })

            if train_id and stops:
                services.append({
                    "train_id": train_id,
                    "train_number": train_num,
                    "train_type": train_type,
                    "priority": priority,
                    "stops": stops
                })
            else:
                errors.append(f"Train element missing ID or stops: {ET.tostring(elem, encoding='unicode')[:80]}")

        valid_count = len(services)
        rejected = total_items - valid_count
        dq_score = round((valid_count / max(1, total_items)) * 100.0, 2)

        res = IngestionResult(
            total_rows=total_items,
            processed_rows=valid_count,
            rejected_rows=rejected,
            dq_score=dq_score,
            errors=errors
        )
        return services, res

    @classmethod
    def ingest_csv_str(cls, csv_text: str) -> Tuple[pd.DataFrame, IngestionResult]:
        """Ingest raw CSV string representation."""
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            return cls.ingest_csv_dataframe(df)
        except Exception as e:
            res = IngestionResult(0, 0, 0, 0.0, [f"CSV Read Error: {str(e)}"])
            return pd.DataFrame(), res
