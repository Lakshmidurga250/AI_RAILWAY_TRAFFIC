"""Synthetic Railway Data Generator with Configurable Random Seed."""
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

class SyntheticDataGenerator:
    """Generates realistic railway operational datasets for AI training and evaluation."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def generate_delay_training_dataset(self, num_samples: int = 2500) -> pd.DataFrame:
        """Generate tabular dataset for training delay prediction models across horizons.
        
        Features:
            - historical_delay_min
            - train_type_encoded (0: High Speed, 1: Intercity, 2: Regional, 3: Commuter, 4: Freight)
            - scheduled_dwell_sec
            - actual_dwell_sec
            - platform_occupancy_rate (0.0 - 1.0)
            - track_congestion_index (0.0 - 1.0)
            - weather_severity (0: Clear, 1: Rain, 2: Snow/Fog, 3: Severe Storm)
            - passenger_load_factor (0.0 - 1.5)
            - preceding_train_delay_min
            - time_of_day_hour (0 - 23)
            - day_of_week (0 - 6)
            - track_gradient_pct (-2.0 to 2.0)
            - infrastructure_health_score (0.5 - 1.0)
            
        Targets:
            - delay_5m, delay_10m, delay_15m, delay_30m, delay_60m
        """
        records = []
        for _ in range(num_samples):
            train_type = random.choice([0, 1, 2, 3, 4])
            hour = random.randint(5, 23)
            is_peak = (7 <= hour <= 9) or (17 <= hour <= 19)
            
            pax_load = np.random.normal(1.1 if is_peak else 0.6, 0.2)
            pax_load = max(0.1, min(1.5, pax_load))
            
            weather = np.random.choice([0, 1, 2, 3], p=[0.7, 0.2, 0.07, 0.03])
            sched_dwell = random.choice([60, 90, 120, 180])
            dwell_excess = max(0, (pax_load - 1.0) * 80 + np.random.normal(0, 15))
            actual_dwell = sched_dwell + dwell_excess
            
            track_congestion = np.random.beta(2, 5) if not is_peak else np.random.beta(4, 3)
            preceding_delay = max(0.0, np.random.exponential(3.0 if track_congestion > 0.6 else 1.0))
            hist_delay = max(0.0, np.random.exponential(2.5))
            
            infra_health = np.random.uniform(0.7, 1.0)
            if random.random() < 0.05:
                infra_health = np.random.uniform(0.4, 0.6)  # minor fault
                
            gradient = np.random.uniform(-1.5, 1.5)
            dow = random.randint(0, 6)

            # Underlying physics/operational delay generation
            base_surge = (
                (hist_delay * 0.45) +
                (preceding_delay * 0.35 * track_congestion) +
                (dwell_excess / 60.0 * 0.5) +
                (weather * 2.2) +
                ((1.0 - infra_health) * 8.0) +
                (1.5 if is_peak else 0.0)
            )

            # Horizons
            delay_5m = max(0.0, base_surge * 0.4 + np.random.normal(0, 0.8))
            delay_10m = max(0.0, base_surge * 0.7 + np.random.normal(0, 1.2))
            delay_15m = max(0.0, base_surge * 1.0 + np.random.normal(0, 1.8))
            delay_30m = max(0.0, base_surge * 1.5 + np.random.normal(0, 2.5))
            delay_60m = max(0.0, base_surge * 2.1 + np.random.normal(0, 4.0))

            records.append({
                "historical_delay_min": round(hist_delay, 2),
                "train_type_encoded": train_type,
                "scheduled_dwell_sec": sched_dwell,
                "actual_dwell_sec": round(actual_dwell, 1),
                "platform_occupancy_rate": round(float(np.random.uniform(0.2, 0.95)), 2),
                "track_congestion_index": round(float(track_congestion), 3),
                "weather_severity": int(weather),
                "passenger_load_factor": round(float(pax_load), 3),
                "preceding_train_delay_min": round(float(preceding_delay), 2),
                "time_of_day_hour": hour,
                "day_of_week": dow,
                "track_gradient_pct": round(float(gradient), 2),
                "infrastructure_health_score": round(float(infra_health), 3),
                "delay_5m": round(float(delay_5m), 2),
                "delay_10m": round(float(delay_10m), 2),
                "delay_15m": round(float(delay_15m), 2),
                "delay_30m": round(float(delay_30m), 2),
                "delay_60m": round(float(delay_60m), 2)
            })

        return pd.DataFrame(records)

    def generate_passenger_demand_dataset(self, num_days: int = 30) -> pd.DataFrame:
        """Generate hourly passenger demand time series for stations."""
        stations = ["ST_NORTH", "ST_METRO", "ST_CENTRAL", "ST_TECH", "ST_AIRPORT", "ST_RIVER", "ST_VALLEY", "ST_HARBOR", "ST_SUMMIT", "ST_SOUTH"]
        base_station_demand = {
            "ST_CENTRAL": 3500, "ST_NORTH": 1800, "ST_SOUTH": 2100, "ST_AIRPORT": 2200,
            "ST_TECH": 1400, "ST_METRO": 1200, "ST_HARBOR": 900, "ST_RIVER": 800,
            "ST_VALLEY": 600, "ST_SUMMIT": 400
        }
        
        start_date = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        records = []

        for d in range(num_days):
            current_date = start_date + timedelta(days=d)
            is_weekend = current_date.weekday() >= 5
            
            for h in range(24):
                time_point = current_date + timedelta(hours=h)
                
                # Diurnal curve
                if 7 <= h <= 9:
                    hour_factor = 2.2 if not is_weekend else 0.8
                elif 16 <= h <= 19:
                    hour_factor = 2.4 if not is_weekend else 1.2
                elif 10 <= h <= 15:
                    hour_factor = 1.1 if not is_weekend else 1.5
                elif 0 <= h <= 4:
                    hour_factor = 0.08
                else:
                    hour_factor = 0.6

                weather_factor = np.random.choice([1.0, 0.92, 0.80, 0.65], p=[0.75, 0.15, 0.07, 0.03])
                
                for st in stations:
                    base = base_station_demand.get(st, 1000)
                    noise = np.random.normal(1.0, 0.08)
                    demand = int(base * hour_factor * weather_factor * noise)
                    demand = max(5, demand)
                    
                    records.append({
                        "timestamp": time_point.isoformat(),
                        "station_id": st,
                        "hour": h,
                        "day_of_week": current_date.weekday(),
                        "is_weekend": int(is_weekend),
                        "passenger_count": demand
                    })

        return pd.DataFrame(records)

synthetic_generator = SyntheticDataGenerator()
