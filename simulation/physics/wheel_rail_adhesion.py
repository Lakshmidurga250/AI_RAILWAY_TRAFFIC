"""Wheel-Rail Contact Mechanics and Adhesion / Wheel-Slide Protection (WSP) Model.

Implements the Polach non-linear contact formulation to compute creepage-dependent
adhesion limits under variable railhead environmental conditions (dry, wet, leaves, ice).
"""
import math
from enum import Enum
from typing import Dict, Any, Tuple


class TrackAdhesionCondition(str, Enum):
    DRY_CLEAN = "DRY_CLEAN"
    DAMP_HUMID = "DAMP_HUMID"
    WET_RAIN = "WET_RAIN"
    LEAVES_ON_LINE = "LEAVES_ON_LINE"
    ICY_FROST = "ICY_FROST"
    GREASY_CONTAMINATED = "GREASY_CONTAMINATED"


class WheelRailAdhesionModel:
    """Polach wheel-rail friction and adhesion limit solver."""

    GRAVITY = 9.81  # m/s^2

    # Baseline friction coefficients per railhead surface condition
    FRICTION_COEFFICIENTS = {
        TrackAdhesionCondition.DRY_CLEAN: 0.40,
        TrackAdhesionCondition.DAMP_HUMID: 0.28,
        TrackAdhesionCondition.WET_RAIN: 0.20,
        TrackAdhesionCondition.LEAVES_ON_LINE: 0.07,
        TrackAdhesionCondition.ICY_FROST: 0.10,
        TrackAdhesionCondition.GREASY_CONTAMINATED: 0.06,
    }

    @classmethod
    def calculate_adhesion_coefficient(
        cls,
        slip_ratio: float,
        speed_kmh: float,
        condition: TrackAdhesionCondition = TrackAdhesionCondition.DRY_CLEAN,
        sanding_active: bool = False
    ) -> float:
        """Compute the dynamic wheel-rail adhesion coefficient mu(s, v).

        Parameters:
            slip_ratio: Longitudinal creepage s = (omega*r - v) / v (-1.0 to 1.0)
            speed_kmh: Train instantaneous velocity in km/h
            condition: Environmental railhead state
            sanding_active: Whether pneumatic sanders are spraying friction enhancer

        Returns:
            Friction coefficient mu in range [0.02, 0.45]
        """
        base_mu = cls.FRICTION_COEFFICIENTS.get(condition, 0.35)

        # Sanding enhances adhesion under low-friction conditions
        if sanding_active and base_mu < 0.25:
            base_mu = min(0.30, base_mu + 0.12)

        # Speed degradation factor (Curtius-Kniffler empirical relation)
        speed_factor = 1.0 / (1.0 + 0.01 * (speed_kmh / 30.0))
        mu_max = base_mu * speed_factor

        abs_s = abs(slip_ratio)
        if abs_s < 1e-5:
            return 0.0

        k_a = 60.0
        k_b = 20.0
        epsilon = k_a * abs_s

        # Normalized Polach adhesion curve
        raw_curve = (2.0 * epsilon / (1.0 + epsilon ** 2)) + ((2.0 / math.pi) * math.atan(k_b * abs_s))
        adhesion_fraction = min(1.0, raw_curve * 0.75)

        # Macro-slip reduction beyond optimum slip point (~2.5% to 3.5% slip)
        if abs_s > 0.03:
            slip_penalty = 1.0 - min(0.40, (abs_s - 0.03) * 3.0)
            adhesion_fraction *= slip_penalty

        mu = mu_max * adhesion_fraction
        return max(0.02, min(0.45, mu))

    @classmethod
    def evaluate_traction_limit(
        cls,
        demanded_tractive_force_n: float,
        adhesive_mass_tons: float,
        speed_kmh: float,
        condition: TrackAdhesionCondition = TrackAdhesionCondition.DRY_CLEAN,
        wsp_enabled: bool = True
    ) -> Dict[str, Any]:
        """Evaluate tractive effort against the physical adhesion limit.

        Implements Wheel Slip Protection (WSP) to prevent runaway wheel spin.
        """
        normal_force_n = (adhesive_mass_tons * 1000.0) * cls.GRAVITY

        # Optimal micro-slip occurs around 1.8% creepage
        optimal_slip = 0.018
        mu_peak = cls.calculate_adhesion_coefficient(optimal_slip, speed_kmh, condition)
        max_adhesion_force_n = mu_peak * normal_force_n

        wheel_slip_detected = False
        sanding_recommended = False
        actual_force_n = demanded_tractive_force_n

        if abs(demanded_tractive_force_n) > max_adhesion_force_n:
            wheel_slip_detected = True
            if wsp_enabled:
                # WSP modulates tractive force to match available peak adhesion
                actual_force_n = math.copysign(max_adhesion_force_n * 0.96, demanded_tractive_force_n)
                if condition in (TrackAdhesionCondition.LEAVES_ON_LINE, TrackAdhesionCondition.GREASY_CONTAMINATED):
                    sanding_recommended = True
            else:
                # Without WSP, macro-spin occurs, collapsing adhesion to sliding friction
                actual_force_n = math.copysign(max_adhesion_force_n * 0.60, demanded_tractive_force_n)

        slip_percentage = 0.0 if not wheel_slip_detected else round(
            ((abs(demanded_tractive_force_n) - max_adhesion_force_n) / max_adhesion_force_n) * 100.0, 1
        )

        return {
            "demanded_force_kn": round(demanded_tractive_force_n / 1000.0, 2),
            "actual_force_kn": round(actual_force_n / 1000.0, 2),
            "max_adhesion_force_kn": round(max_adhesion_force_n / 1000.0, 2),
            "peak_adhesion_coefficient": round(mu_peak, 3),
            "rail_condition": condition.value,
            "wheel_slip_detected": wheel_slip_detected,
            "wsp_active": wheel_slip_detected and wsp_enabled,
            "sanding_recommended": sanding_recommended,
            "slip_overload_percentage": slip_percentage
        }
