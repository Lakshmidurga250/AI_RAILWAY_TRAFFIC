"""Passenger Demand Forecasting and Anomaly Detection Engine."""
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from simulation.network.graph import RailwayNetwork

class DemandPredictor:
    """Predicts hourly passenger demand, peak flow windows, and surges."""

    BASE_DEMAND = {
        "ST_CENTRAL": 3200,
        "ST_NORTH": 1800,
        "ST_SOUTH": 2100,
        "ST_AIRPORT": 2400,
        "ST_TECH": 1500,
        "ST_METRO": 1300,
        "ST_HARBOR": 950,
        "ST_RIVER": 750,
        "ST_VALLEY": 550,
        "ST_SUMMIT": 350
    }

    @classmethod
    def predict_station_demand(
        cls,
        station_id: str,
        network: Optional[RailwayNetwork] = None,
        horizon_hours: int = 24
    ) -> Dict[str, Any]:
        """Generate 24-hour demand curve, peak intervals, and anomaly detection."""
        base = cls.BASE_DEMAND.get(station_id, 1200)
        station_name = station_id
        current_occ = int(base * 0.35)
        capacity = 10000

        if network:
            st = network.stations.get(station_id)
            if st:
                station_name = st.name
                current_occ = st.current_occupancy
                capacity = st.passenger_capacity

        now = datetime.now(timezone.utc)
        hourly_forecast = []
        peak_hours = []
        anomalies = []

        for h in range(horizon_hours):
            fc_time = now + timedelta(hours=h)
            hour_of_day = fc_time.hour
            is_weekend = fc_time.weekday() >= 5

            # Diurnal multipliers
            if 7 <= hour_of_day <= 9:
                factor = 2.4 if not is_weekend else 0.85
            elif 16 <= hour_of_day <= 19:
                factor = 2.6 if not is_weekend else 1.3
            elif 10 <= hour_of_day <= 15:
                factor = 1.15 if not is_weekend else 1.6
            elif 0 <= hour_of_day <= 4:
                factor = 0.07
            else:
                factor = 0.70

            predicted_pax = int(base * factor)
            lower_ci = int(predicted_pax * 0.85)
            upper_ci = int(predicted_pax * 1.15)

            is_peak = (7 <= hour_of_day <= 9) or (16 <= hour_of_day <= 19)
            if is_peak and hour_of_day not in peak_hours:
                peak_hours.append(hour_of_day)

            # Simulated anomaly detection (e.g. event surge around evening)
            if hour_of_day == 18 and not is_weekend:
                anomalies.append({
                    "hour": hour_of_day,
                    "timestamp": fc_time.isoformat(),
                    "severity": "WARNING",
                    "type": "EVENING_COMMUTE_SURGE",
                    "expected": predicted_pax,
                    "confidence": 0.89,
                    "message": "Potential station platform crowding expected between 17:30 and 18:30"
                })

            hourly_forecast.append({
                "hour": hour_of_day,
                "timestamp": fc_time.isoformat(),
                "forecast_demand": predicted_pax,
                "lower_bound": lower_ci,
                "upper_bound": upper_ci,
                "is_peak": is_peak
            })

        return {
            "station_id": station_id,
            "station_name": station_name,
            "current_occupancy": current_occ,
            "capacity": capacity,
            "hourly_forecast": hourly_forecast,
            "peak_hours": sorted(peak_hours),
            "anomalies_detected": anomalies,
            "confidence_interval": {"lower_percent": 85.0, "upper_percent": 115.0},
            "timestamp": now.isoformat()
        }

demand_predictor = DemandPredictor()
