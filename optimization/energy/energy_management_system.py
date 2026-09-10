"""
Energy Management System for Railway Traction.

Comprehensive energy optimization and monitoring for electric railway traction:

  - Traction energy consumption modelling (Davis equation + gradient + curve resistance)
  - Regenerative braking energy harvesting and grid feed-back
  - Station-level energy demand aggregation
  - Peak demand shaving and load levelling strategies
  - Substation voltage profile management
  - Energy billing and tariff optimisation (TOD / off-peak scheduling)
  - Carbon footprint computation (kgCO₂ per passenger-km)
  - Solar and hybrid energy integration
  - Train eco-driving advisory (coasting curves, speed profiles)
  - Network-wide energy KPI dashboard
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

GRAVITY_MS2          = 9.81
STEEL_DENSITY        = 7850.0     # kg/m³
GRID_CARBON_FACTOR   = 0.716      # kgCO₂/kWh (India average 2024)
AC_25KV_EFFICIENCY   = 0.88       # substation + OHE losses
REGEN_RETURN_FACTOR  = 0.72       # fraction of braking energy returned to grid
LOCO_AUXILIARY_KW    = 35.0       # auxiliary load per loco (HVAC, lighting etc.)
COACH_AUXILIARY_KW   = 8.5        # per coach (lighting, fans, AC if fitted)


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class TractionPowerType(str, Enum):
    AC_25KV    = "AC25"
    DC_1500V   = "DC1500"
    DC_750V    = "DC750"
    DIESEL     = "DIESEL"
    HYBRID     = "HYBRID"
    HYDROGEN   = "H2"


class EcoDriverAdvisory(str, Enum):
    ACCELERATE     = "ACCELERATE"
    MAINTAIN       = "MAINTAIN"
    COAST          = "COAST"
    BRAKE          = "BRAKE"
    EMERGENCY_BRAKE = "EMERGENCY_BRAKE"
    HOLD           = "HOLD"


class TariffPeriod(str, Enum):
    PEAK          = "PEAK"        # 06:00-10:00, 18:00-22:00
    OFF_PEAK      = "OFF_PEAK"    # 22:00-06:00
    STANDARD      = "STANDARD"    # 10:00-18:00


# ─────────────────────────────────────────────────────────────────────────────
# Tariff structure (indicative Indian Railway traction tariff ₹/kWh)
# ─────────────────────────────────────────────────────────────────────────────

TARIFF_RATE = {
    TariffPeriod.PEAK:     8.50,
    TariffPeriod.STANDARD: 6.20,
    TariffPeriod.OFF_PEAK: 4.10,
}


def get_tariff_period(hour: int) -> TariffPeriod:
    if 6 <= hour < 10 or 18 <= hour < 22:
        return TariffPeriod.PEAK
    if 22 <= hour or hour < 6:
        return TariffPeriod.OFF_PEAK
    return TariffPeriod.STANDARD


# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TrainResistanceParams:
    """Davis equation parameters for traction resistance computation."""
    mass_tonnes:    float       # gross mass including load
    a_coeff:        float = 0.6    # Davis A (N/tonne) — rolling resistance
    b_coeff:        float = 0.006  # Davis B (N/tonne/km/h) — bearing friction
    c_coeff:        float = 0.00035 # Davis C (N/tonne/(km/h)²) — aerodynamic
    num_axles:      int   = 4
    frontal_area_m2: float = 10.0

    def davis_resistance_kn(self, speed_kmh: float) -> float:
        """Total train resistance in kN at given speed."""
        r = (self.a_coeff +
             self.b_coeff * speed_kmh +
             self.c_coeff * speed_kmh ** 2)
        return r * self.mass_tonnes / 1000.0   # kN

    def gradient_resistance_kn(self, gradient_pct: float) -> float:
        """Gradient resistance force in kN. Positive = uphill."""
        return self.mass_tonnes * GRAVITY_MS2 * gradient_pct / 100.0 / 1000.0

    def curve_resistance_kn(self, radius_m: float) -> float:
        """Flange/curve resistance in kN. 0 if straight."""
        if radius_m <= 0:
            return 0.0
        # Approximate: 6.3 / R (N/tonne) for broad gauge
        return 6.3 * self.mass_tonnes / radius_m / 1000.0

    def total_resistance_kn(self, speed_kmh: float,
                            gradient_pct: float = 0.0,
                            curve_radius_m: float = 0.0) -> float:
        return (self.davis_resistance_kn(speed_kmh) +
                self.gradient_resistance_kn(gradient_pct) +
                self.curve_resistance_kn(curve_radius_m))


@dataclass
class EnergySegment:
    """Energy consumption record for one track segment of a journey."""
    segment_id:        str
    train_id:          str
    from_station:      str
    to_station:        str
    distance_km:       float
    avg_speed_kmh:     float
    gradient_pct:      float
    traction_kwh:      float    # motoring energy drawn
    regen_kwh:         float    # regenerative braking energy recovered
    auxiliary_kwh:     float    # auxiliary systems
    net_kwh:           float    # traction - regen + auxiliary
    duration_minutes:  float
    tariff_period:     TariffPeriod
    cost_inr:          float
    co2_kg:            float
    timestamp:         datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def specific_energy_kwh_per_km(self) -> float:
        return self.net_kwh / max(self.distance_km, 0.001)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id":        self.segment_id,
            "train_id":          self.train_id,
            "from_station":      self.from_station,
            "to_station":        self.to_station,
            "distance_km":       round(self.distance_km, 2),
            "avg_speed_kmh":     round(self.avg_speed_kmh, 1),
            "traction_kwh":      round(self.traction_kwh, 2),
            "regen_kwh":         round(self.regen_kwh, 2),
            "auxiliary_kwh":     round(self.auxiliary_kwh, 2),
            "net_kwh":           round(self.net_kwh, 2),
            "specific_energy":   round(self.specific_energy_kwh_per_km, 3),
            "tariff_period":     self.tariff_period.value,
            "cost_inr":          round(self.cost_inr, 2),
            "co2_kg":            round(self.co2_kg, 2),
            "duration_min":      round(self.duration_minutes, 1),
            "timestamp":         self.timestamp.isoformat(),
        }


@dataclass
class SubstationProfile:
    """Voltage and load profile for a traction substation."""
    substation_id:   str
    name:            str
    location_km:     float
    zone_code:       str
    rated_mva:       float
    voltage_kv:      float = 25.0
    current_load_mw: float = 0.0
    voltage_pu:      float = 1.0   # per-unit voltage (1.0 = nominal)
    regen_injection_mw: float = 0.0

    @property
    def load_factor(self) -> float:
        rated_mw = self.rated_mva * 0.9  # assuming 0.9 PF
        return self.current_load_mw / max(rated_mw, 0.001)

    @property
    def is_overloaded(self) -> bool:
        return self.load_factor > 0.95

    @property
    def voltage_status(self) -> str:
        if self.voltage_pu < 0.90:
            return "LOW_VOLTAGE"
        if self.voltage_pu > 1.10:
            return "HIGH_VOLTAGE"
        return "NORMAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "substation_id":   self.substation_id,
            "name":            self.name,
            "location_km":     self.location_km,
            "zone":            self.zone_code,
            "rated_mva":       self.rated_mva,
            "current_load_mw": round(self.current_load_mw, 2),
            "load_factor":     round(self.load_factor, 3),
            "voltage_pu":      round(self.voltage_pu, 4),
            "voltage_status":  self.voltage_status,
            "regen_injection_mw": round(self.regen_injection_mw, 2),
            "is_overloaded":   self.is_overloaded,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Energy Calculator
# ─────────────────────────────────────────────────────────────────────────────

class TractionEnergyCalculator:
    """
    Computes traction energy consumption for a train on a route segment.

    Based on:
    - Davis equation resistance
    - Gradient forces
    - Curve forces
    - Trapezoidal speed-time integration
    - Regenerative braking recovery
    - Auxiliary loads
    """

    def __init__(self, efficiency: float = AC_25KV_EFFICIENCY) -> None:
        self.efficiency = efficiency

    def compute_segment_energy(
        self,
        train_id:       str,
        from_station:   str,
        to_station:     str,
        distance_km:    float,
        speed_profile:  List[Tuple[float, float]],  # [(time_s, speed_kmh)]
        resistance:     TrainResistanceParams,
        gradient_pct:   float = 0.0,
        curve_radius_m: float = 0.0,
        num_coaches:    int   = 16,
        power_type:     TractionPowerType = TractionPowerType.AC_25KV,
        at_time:        Optional[datetime] = None,
    ) -> EnergySegment:
        """Compute energy for one segment using trapezoidal speed profile integration."""
        now = at_time or datetime.now(timezone.utc)
        tariff = get_tariff_period(now.hour)

        traction_kwh = 0.0
        regen_kwh    = 0.0
        prev_t, prev_v = speed_profile[0] if speed_profile else (0.0, 0.0)
        total_time_s = 0.0

        for t_s, v_kmh in speed_profile[1:]:
            dt  = t_s - prev_t
            avg_v = (v_kmh + prev_v) / 2.0   # km/h
            if dt <= 0:
                prev_t, prev_v = t_s, v_kmh
                continue

            # Acceleration (m/s²)
            dv_ms = (v_kmh - prev_v) / 3.6
            accel = dv_ms / max(dt, 0.001)

            # Forces (kN)
            F_resist = resistance.total_resistance_kn(avg_v, gradient_pct, curve_radius_m)
            F_accel  = resistance.mass_tonnes * accel       # kN (F = ma)
            F_total  = F_resist + F_accel                   # kN

            dist_m   = avg_v / 3.6 * dt                     # metres
            work_kj  = F_total * dist_m                      # kJ = kN × m

            if work_kj >= 0:
                # Motoring
                traction_kwh += work_kj / 3600.0 / self.efficiency
            else:
                # Braking → regeneration
                regen_kwh += abs(work_kj) / 3600.0 * REGEN_RETURN_FACTOR

            prev_t, prev_v = t_s, v_kmh
            total_time_s  += dt

        # Auxiliary energy
        duration_h    = total_time_s / 3600.0
        auxiliary_kwh = (LOCO_AUXILIARY_KW + num_coaches * COACH_AUXILIARY_KW) * duration_h

        # Net
        net_kwh = traction_kwh - regen_kwh + auxiliary_kwh

        # Cost and emissions
        rate    = TARIFF_RATE[tariff]
        cost    = net_kwh * rate
        co2_kg  = net_kwh * GRID_CARBON_FACTOR

        seg_id = f"SEG_{train_id}_{from_station}_{to_station}"
        return EnergySegment(
            segment_id        = seg_id,
            train_id          = train_id,
            from_station      = from_station,
            to_station        = to_station,
            distance_km       = distance_km,
            avg_speed_kmh     = sum(v for _, v in speed_profile) / max(len(speed_profile), 1),
            gradient_pct      = gradient_pct,
            traction_kwh      = traction_kwh,
            regen_kwh         = regen_kwh,
            auxiliary_kwh     = auxiliary_kwh,
            net_kwh           = max(0.0, net_kwh),
            duration_minutes  = total_time_s / 60.0,
            tariff_period     = tariff,
            cost_inr          = cost,
            co2_kg            = co2_kg,
        )

    def estimate_segment_energy_simple(
        self,
        train_id:      str,
        from_station:  str,
        to_station:    str,
        distance_km:   float,
        avg_speed_kmh: float,
        mass_tonnes:   float,
        gradient_pct:  float = 0.0,
        num_coaches:   int   = 16,
    ) -> EnergySegment:
        """Simplified energy estimate without full speed profile."""
        resistance = TrainResistanceParams(mass_tonnes=mass_tonnes)
        duration_s = (distance_km / max(avg_speed_kmh, 1.0)) * 3600.0
        speed_profile = [(0.0, avg_speed_kmh), (duration_s, avg_speed_kmh)]
        return self.compute_segment_energy(
            train_id, from_station, to_station, distance_km,
            speed_profile, resistance, gradient_pct,
            num_coaches=num_coaches,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Eco-Driving Advisor
# ─────────────────────────────────────────────────────────────────────────────

class EcoDrivingAdvisor:
    """
    Generates real-time eco-driving advisories to minimise energy consumption
    while maintaining schedule adherence.

    Strategy: Optimal speed trajectory using a simplified EETC
    (Energy-efficient Train Control) coasting algorithm.
    """

    def __init__(self, time_buffer_pct: float = 5.0) -> None:
        self.time_buffer_pct = time_buffer_pct  # allowable schedule slack

    def get_advisory(
        self,
        current_speed_kmh:  float,
        target_speed_kmh:   float,
        distance_to_stop_km: float,
        gradient_pct:       float,
        schedule_slack_s:   float,
        resistance:         TrainResistanceParams,
    ) -> Dict[str, Any]:
        """Return the recommended driving mode for the current moment."""
        # Braking distance estimation
        braking_dist_km = current_speed_kmh ** 2 / (2 * 1.0 * 3600) * 0.1  # simplified

        advisory: EcoDriverAdvisory
        if distance_to_stop_km <= braking_dist_km * 1.2:
            advisory = EcoDriverAdvisory.BRAKE
        elif schedule_slack_s > 0 and current_speed_kmh >= target_speed_kmh * 0.95:
            advisory = EcoDriverAdvisory.COAST
        elif current_speed_kmh < target_speed_kmh * 0.90:
            advisory = EcoDriverAdvisory.ACCELERATE
        else:
            advisory = EcoDriverAdvisory.MAINTAIN

        # Energy savings from coasting (estimated)
        coasting_saving_pct = (
            15.0 if advisory == EcoDriverAdvisory.COAST else
             8.0 if advisory == EcoDriverAdvisory.MAINTAIN else
             0.0
        )

        return {
            "advisory":             advisory.value,
            "current_speed_kmh":    round(current_speed_kmh, 1),
            "target_speed_kmh":     round(target_speed_kmh, 1),
            "distance_to_stop_km":  round(distance_to_stop_km, 3),
            "schedule_slack_s":     round(schedule_slack_s, 0),
            "gradient_pct":         round(gradient_pct, 2),
            "estimated_saving_pct": coasting_saving_pct,
            "rationale":            self._rationale(advisory, gradient_pct, schedule_slack_s),
        }

    @staticmethod
    def _rationale(advisory: EcoDriverAdvisory, gradient: float, slack: float) -> str:
        if advisory == EcoDriverAdvisory.COAST:
            return f"Slack {slack:.0f}s available; coasting saves ~15% energy"
        if advisory == EcoDriverAdvisory.BRAKE:
            return "Approaching stop; apply regenerative braking"
        if advisory == EcoDriverAdvisory.ACCELERATE:
            return f"Below target speed; accelerate {'against' if gradient > 0 else 'with'} gradient"
        return "Maintain current speed profile"

    def generate_optimal_speed_profile(
        self,
        distance_km:   float,
        max_speed_kmh: float,
        start_speed:   float = 0.0,
        end_speed:     float = 0.0,
        time_limit_s:  Optional[float] = None,
        num_points:    int = 20,
    ) -> List[Tuple[float, float]]:
        """
        Generate an approximate optimal (energy-efficient) speed profile.
        Uses three phases: accelerate → cruise/coast → brake.
        """
        accel_rate = 0.6  # m/s²
        brake_rate  = 0.8  # m/s²

        vmax = max_speed_kmh / 3.6
        t_accel = vmax / accel_rate
        d_accel = 0.5 * accel_rate * t_accel ** 2
        t_brake = vmax / brake_rate
        d_brake = 0.5 * brake_rate * t_brake ** 2
        d_total = distance_km * 1000
        d_cruise = max(0.0, d_total - d_accel - d_brake)
        t_cruise = d_cruise / max(vmax, 0.001)
        total_time = t_accel + t_cruise + t_brake

        profile: List[Tuple[float, float]] = []
        step = total_time / max(num_points - 1, 1)
        for i in range(num_points):
            t = i * step
            if t <= t_accel:
                v_ms = accel_rate * t
            elif t <= t_accel + t_cruise:
                v_ms = vmax
            else:
                t_in_brake = t - t_accel - t_cruise
                v_ms = max(0.0, vmax - brake_rate * t_in_brake)
            profile.append((t, v_ms * 3.6))

        return profile


# ─────────────────────────────────────────────────────────────────────────────
# Peak Demand Shaver
# ─────────────────────────────────────────────────────────────────────────────

class PeakDemandShaver:
    """
    Identifies and mitigates peak demand periods across a zone's traction network.

    Strategy:
    - Identify trains that can be rescheduled from peak to off-peak tariff windows
    - Quantify demand shaving potential
    - Recommend departure time adjustments
    """

    def __init__(self, peak_threshold_mw: float = 50.0) -> None:
        self.peak_threshold_mw = peak_threshold_mw

    def analyse_demand_profile(
        self,
        hourly_demand_mw: List[float],   # 24-element list, index = hour
    ) -> Dict[str, Any]:
        peak_hours  = [h for h, mw in enumerate(hourly_demand_mw) if mw > self.peak_threshold_mw]
        valley_hours = [h for h, mw in enumerate(hourly_demand_mw) if mw < self.peak_threshold_mw * 0.6]
        shaving_potential_mwh = sum(
            max(0, mw - self.peak_threshold_mw)
            for mw in hourly_demand_mw
        )
        cost_saving_inr = sum(
            max(0, mw - self.peak_threshold_mw) *
            (TARIFF_RATE[TariffPeriod.PEAK] - TARIFF_RATE[TariffPeriod.OFF_PEAK])
            for h, mw in enumerate(hourly_demand_mw)
            if get_tariff_period(h) == TariffPeriod.PEAK
        )
        return {
            "peak_hours":               peak_hours,
            "valley_hours":             valley_hours,
            "peak_demand_mw":           round(max(hourly_demand_mw), 2),
            "avg_demand_mw":            round(sum(hourly_demand_mw) / 24, 2),
            "load_factor":              round(sum(hourly_demand_mw) / 24 / max(hourly_demand_mw, 1), 3),
            "shaving_potential_mwh":    round(shaving_potential_mwh, 2),
            "estimated_saving_inr":     round(cost_saving_inr * 1000, 0),
            "recommended_action":       (
                "Reschedule freight trains to valley hours" if shaving_potential_mwh > 5
                else "Peak demand within acceptable range"
            ),
        }

    def recommend_departure_shifts(
        self,
        train_schedule: List[Dict[str, Any]],  # [{train_id, hour, mw_demand}]
        max_shift_hours: int = 2,
    ) -> List[Dict[str, Any]]:
        recommendations = []
        for t in train_schedule:
            h   = t.get("hour", 0)
            mw  = t.get("mw_demand", 0.0)
            ttype = get_tariff_period(h)
            if ttype == TariffPeriod.PEAK:
                for shift in range(1, max_shift_hours + 1):
                    new_h = (h + shift) % 24
                    new_t = get_tariff_period(new_h)
                    if new_t != TariffPeriod.PEAK:
                        saving = mw * (TARIFF_RATE[TariffPeriod.PEAK] - TARIFF_RATE[new_t])
                        recommendations.append({
                            "train_id":         t["train_id"],
                            "original_hour":    h,
                            "recommended_hour": new_h,
                            "shift_minutes":    shift * 60,
                            "new_tariff":       new_t.value,
                            "saving_inr_per_trip": round(saving * mw * 0.5, 0),
                        })
                        break
        return recommendations


# ─────────────────────────────────────────────────────────────────────────────
# Energy Management System
# ─────────────────────────────────────────────────────────────────────────────

class EnergyManagementSystem:
    """
    Central energy management system for a railway zone.

    Integrates energy calculation, eco-driving advice, substation monitoring,
    peak demand shaving, and comprehensive energy KPI reporting.
    """

    def __init__(self, zone_code: str) -> None:
        self.zone_code        = zone_code
        self.calculator       = TractionEnergyCalculator()
        self.eco_advisor      = EcoDrivingAdvisor()
        self.demand_shaver    = PeakDemandShaver()
        self._segments:        List[EnergySegment]    = []
        self._substations:     Dict[str, SubstationProfile] = {}
        self._hourly_demand:   List[float]            = [0.0] * 24
        self._solar_kwh_today: float                  = 0.0

    # ── Substation management ─────────────────────────────────────────────

    def register_substation(self, sub: SubstationProfile) -> None:
        self._substations[sub.substation_id] = sub

    def update_substation_load(self, sub_id: str, load_mw: float,
                               regen_mw: float = 0.0, voltage_pu: float = 1.0) -> Optional[Dict]:
        sub = self._substations.get(sub_id)
        if not sub:
            return None
        sub.current_load_mw   = load_mw
        sub.regen_injection_mw = regen_mw
        sub.voltage_pu         = voltage_pu
        hour = datetime.now(timezone.utc).hour
        self._hourly_demand[hour] = max(self._hourly_demand[hour], load_mw)
        if sub.is_overloaded:
            logger.warning("Substation %s overloaded: %.1f MW (%.0f%% load factor)",
                           sub_id, load_mw, sub.load_factor * 100)
        return sub.to_dict()

    # ── Energy logging ────────────────────────────────────────────────────

    def log_segment(self, segment: EnergySegment) -> None:
        self._segments.append(segment)

    def log_simple_journey(
        self,
        train_id:      str,
        from_station:  str,
        to_station:    str,
        distance_km:   float,
        avg_speed_kmh: float,
        mass_tonnes:   float,
        gradient_pct:  float = 0.0,
        num_coaches:   int   = 16,
    ) -> EnergySegment:
        seg = self.calculator.estimate_segment_energy_simple(
            train_id, from_station, to_station, distance_km,
            avg_speed_kmh, mass_tonnes, gradient_pct, num_coaches
        )
        self.log_segment(seg)
        return seg

    def add_solar_generation(self, kwh: float) -> None:
        self._solar_kwh_today += kwh

    # ── Reporting ─────────────────────────────────────────────────────────

    def get_zone_energy_kpi(self, for_date: Optional[date] = None) -> Dict[str, Any]:
        today_segs = self._segments   # simplified — no date filter for demo
        total_traction  = sum(s.traction_kwh  for s in today_segs)
        total_regen     = sum(s.regen_kwh     for s in today_segs)
        total_aux       = sum(s.auxiliary_kwh for s in today_segs)
        total_net       = sum(s.net_kwh       for s in today_segs)
        total_cost      = sum(s.cost_inr      for s in today_segs)
        total_co2       = sum(s.co2_kg        for s in today_segs)
        total_dist      = sum(s.distance_km   for s in today_segs)
        specific_energy = total_net / max(total_dist, 1.0)
        regen_pct       = total_regen / max(total_traction, 1.0) * 100.0
        solar_offset_pct = self._solar_kwh_today / max(total_net, 1.0) * 100.0

        sub_alerts = [
            s.to_dict() for s in self._substations.values()
            if s.is_overloaded or s.voltage_status != "NORMAL"
        ]

        demand_analysis = self.demand_shaver.analyse_demand_profile(self._hourly_demand)

        return {
            "zone":                   self.zone_code,
            "date":                   (for_date or date.today()).isoformat(),
            "segments_analysed":      len(today_segs),
            "total_traction_kwh":     round(total_traction, 1),
            "total_regen_kwh":        round(total_regen, 1),
            "total_auxiliary_kwh":    round(total_aux, 1),
            "total_net_kwh":          round(total_net, 1),
            "regen_recovery_pct":     round(regen_pct, 1),
            "specific_energy_kwh_km": round(specific_energy, 3),
            "total_distance_km":      round(total_dist, 1),
            "total_cost_inr":         round(total_cost, 0),
            "total_co2_kg":           round(total_co2, 1),
            "solar_kwh_today":        round(self._solar_kwh_today, 1),
            "solar_offset_pct":       round(solar_offset_pct, 1),
            "substations_monitored":  len(self._substations),
            "substation_alerts":      sub_alerts,
            "demand_analysis":        demand_analysis,
            "timestamp":              datetime.now(timezone.utc).isoformat(),
        }

    def get_substation_dashboard(self) -> List[Dict[str, Any]]:
        return sorted(
            [s.to_dict() for s in self._substations.values()],
            key=lambda x: x["load_factor"], reverse=True
        )

    def get_eco_advisory(
        self,
        train_id:           str,
        current_speed_kmh:  float,
        target_speed_kmh:   float,
        distance_to_stop_km: float,
        gradient_pct:       float = 0.0,
        schedule_slack_s:   float = 0.0,
        mass_tonnes:        float = 600.0,
    ) -> Dict[str, Any]:
        resistance = TrainResistanceParams(mass_tonnes=mass_tonnes)
        return self.eco_advisor.get_advisory(
            current_speed_kmh, target_speed_kmh,
            distance_to_stop_km, gradient_pct, schedule_slack_s, resistance
        )

    def generate_optimal_profile(
        self,
        distance_km:   float,
        max_speed_kmh: float,
        num_points:    int = 20,
    ) -> List[Dict[str, Any]]:
        profile = self.eco_advisor.generate_optimal_speed_profile(
            distance_km, max_speed_kmh, num_points=num_points
        )
        return [{"time_s": round(t, 1), "speed_kmh": round(v, 1)} for t, v in profile]


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def build_sample_ems(zone_code: str = "NR") -> EnergyManagementSystem:
    """Build a sample EMS pre-loaded with substations and representative journeys."""
    import random
    ems = EnergyManagementSystem(zone_code)

    # Register substations
    for i in range(12):
        sub = SubstationProfile(
            substation_id  = f"SS_{zone_code}_{i+1:02d}",
            name           = f"{zone_code} TSS {i+1}",
            location_km    = round(i * 40 + random.uniform(0, 20), 1),
            zone_code      = zone_code,
            rated_mva      = random.choice([20.0, 40.0, 60.0]),
            current_load_mw = round(random.uniform(5, 45), 2),
            voltage_pu     = round(random.uniform(0.93, 1.07), 4),
            regen_injection_mw = round(random.uniform(0, 5), 2),
        )
        ems.register_substation(sub)

    # Simulate some journeys
    routes = [
        ("NDLS", "BCT", 1380, 90, 800),
        ("NDLS", "HWH", 1450, 85, 900),
        ("MAS",  "SC",   470, 80, 700),
        ("BCT",  "JP",   620, 75, 750),
        ("LJN",  "PNBE", 350, 70, 680),
    ]
    for from_s, to_s, dist, speed, mass in routes:
        for tid_num in range(3):
            seg = ems.log_simple_journey(
                train_id      = f"T{random.randint(10000,99999)}",
                from_station  = from_s,
                to_station    = to_s,
                distance_km   = dist + random.uniform(-50, 50),
                avg_speed_kmh = speed + random.uniform(-10, 10),
                mass_tonnes   = mass,
                gradient_pct  = random.uniform(-0.5, 0.5),
                num_coaches   = random.randint(18, 24),
            )

    # Solar contribution
    ems.add_solar_generation(round(random.uniform(200, 800), 1))

    # Populate hourly demand
    from simulation.national_scale.national_coordinator import HOURLY_DEMAND_PROFILE  # reuse curve
    for h in range(24):
        ems._hourly_demand[h] = round(HOURLY_DEMAND_PROFILE[h] * 30 * random.uniform(0.8, 1.2), 2)

    return ems


# Module-level singleton for Northern Railway
try:
    from simulation.national_scale.national_coordinator import HOURLY_DEMAND_PROFILE
except ImportError:
    HOURLY_DEMAND_PROFILE = [1.0] * 24

default_ems = EnergyManagementSystem("NR")
