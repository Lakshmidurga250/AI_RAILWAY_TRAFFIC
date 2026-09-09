"""Catenary 25kV AC Traction Power Flow and Pantograph Voltage Sag Simulation.

Models electrical substation feeding sections, catenary transmission line impedance,
pantograph voltage drops under heavy acceleration, transmission I^2*R losses, and
regenerative energy receptivity across corridor electrical feeder sections (EN 50163).
"""
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TractionElectricalState:
    train_id: str
    location_km: float
    mechanical_power_kw: float
    auxiliary_power_kw: float
    electrical_power_kw: float
    current_amperes: float
    pantograph_voltage_kv: float
    line_loss_kw: float
    regenerative_receptive: bool


class CatenarySubstationNetwork:
    """Solves electrical power flow for electrified railway feeder sections."""

    NOMINAL_SUBSTATION_VOLTAGE_KV = 27.5  # Standard 25 kV AC no-load substation voltage
    MIN_ALLOWABLE_VOLTAGE_KV = 19.0       # EN 50163 minimum operational limit
    MAX_ALLOWABLE_VOLTAGE_KV = 29.0       # Overvoltage tripping limit

    # Typical 25kV catenary + contact wire loop resistance
    CATENARY_RESISTANCE_OHM_PER_KM = 0.18  # Ohm/km
    POWER_FACTOR = 0.95                   # Modern IGBT inverter displacement power factor
    CONVERTER_EFFICIENCY = 0.92           # Combined traction transformer + inverter efficiency

    def __init__(
        self,
        substation_locations_km: Optional[List[float]] = None,
        feed_section_length_km: float = 35.0
    ):
        # Default substations spaced along corridor
        self.substation_locations_km = substation_locations_km or [0.0, 35.0, 70.0]
        self.feed_section_length_km = feed_section_length_km

    def solve_power_flow(
        self,
        train_demands: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Solve pantograph voltages, current draws, and line losses for all corridor trains.

        Parameters:
            train_demands: List of dicts with:
                - train_id: str
                - location_km: float
                - mechanical_power_kw: float (positive = accelerating, negative = braking)
                - auxiliary_power_kw: float (HVAC, systems ~ 40 kW)

        Returns:
            Dict containing electrical states for all trains and total grid load/losses.
        """
        results: List[TractionElectricalState] = []
        total_grid_demand_mw = 0.0
        total_line_loss_mw = 0.0
        total_regen_recovered_mw = 0.0

        for t in train_demands:
            loc = t["location_km"]
            p_mech = t["mechanical_power_kw"]
            p_aux = t.get("auxiliary_power_kw", 40.0)

            # Find nearest feeding substation
            dists = [abs(loc - sub_loc) for sub_loc in self.substation_locations_km]
            dist_to_sub_km = min(dists) if dists else 10.0

            # Line resistance between substation and pantograph
            r_line = dist_to_sub_km * self.CATENARY_RESISTANCE_OHM_PER_KM

            if p_mech >= 0:
                # Traction mode
                p_traction_elec = p_mech / self.CONVERTER_EFFICIENCY
                p_total_kw = p_traction_elec + p_aux
                # Iterative voltage sag calculation: V = V_sub - (I * R)
                v_panto_kv = self.NOMINAL_SUBSTATION_VOLTAGE_KV
                # Approximate 2-step iteration for voltage sag
                current_a = (p_total_kw * 1000.0) / (max(10.0, v_panto_kv * 1000.0) * self.POWER_FACTOR)
                v_drop_kv = (current_a * r_line) / 1000.0
                v_panto_kv = max(self.MIN_ALLOWABLE_VOLTAGE_KV, self.NOMINAL_SUBSTATION_VOLTAGE_KV - v_drop_kv)
                # Recompute current with actual sagged voltage
                current_a = (p_total_kw * 1000.0) / (max(10.0, v_panto_kv * 1000.0) * self.POWER_FACTOR)
                line_loss_kw = ((current_a ** 2) * r_line) / 1000.0

                is_receptive = False
                total_grid_demand_mw += (p_total_kw + line_loss_kw) / 1000.0
                total_line_loss_mw += line_loss_kw / 1000.0

            else:
                # Regenerative Braking mode
                p_regen_elec = abs(p_mech) * self.CONVERTER_EFFICIENCY
                p_net_kw = p_regen_elec - p_aux

                if p_net_kw > 0:
                    # Current pushed back into catenary
                    current_a = (p_net_kw * 1000.0) / (self.NOMINAL_SUBSTATION_VOLTAGE_KV * 1000.0 * self.POWER_FACTOR)
                    v_rise_kv = (current_a * r_line) / 1000.0
                    v_panto_kv = min(self.MAX_ALLOWABLE_VOLTAGE_KV, self.NOMINAL_SUBSTATION_VOLTAGE_KV + v_rise_kv)
                    line_loss_kw = ((current_a ** 2) * r_line) / 1000.0
                    is_receptive = v_panto_kv < self.MAX_ALLOWABLE_VOLTAGE_KV
                    total_regen_recovered_mw += (p_net_kw - line_loss_kw) / 1000.0
                else:
                    v_panto_kv = self.NOMINAL_SUBSTATION_VOLTAGE_KV
                    current_a = 0.0
                    line_loss_kw = 0.0
                    is_receptive = True

                p_total_kw = -p_net_kw

            results.append(TractionElectricalState(
                train_id=t["train_id"],
                location_km=round(loc, 2),
                mechanical_power_kw=round(p_mech, 1),
                auxiliary_power_kw=round(p_aux, 1),
                electrical_power_kw=round(p_total_kw, 1),
                current_amperes=round(current_a, 1),
                pantograph_voltage_kv=round(v_panto_kv, 2),
                line_loss_kw=round(line_loss_kw, 2),
                regenerative_receptive=is_receptive
            ))

        voltage_sag_critical = any(s.pantograph_voltage_kv <= self.MIN_ALLOWABLE_VOLTAGE_KV + 0.5 for s in results)

        return {
            "substation_count": len(self.substation_locations_km),
            "total_grid_demand_mw": round(total_grid_demand_mw, 2),
            "total_line_loss_mw": round(total_line_loss_mw, 3),
            "total_regen_recovered_mw": round(total_regen_recovered_mw, 2),
            "voltage_sag_alert": voltage_sag_critical,
            "train_states": [
                {
                    "train_id": s.train_id,
                    "location_km": s.location_km,
                    "electrical_power_kw": s.electrical_power_kw,
                    "current_amperes": s.current_amperes,
                    "pantograph_voltage_kv": s.pantograph_voltage_kv,
                    "line_loss_kw": s.line_loss_kw,
                    "regenerative_receptive": s.regenerative_receptive
                }
                for s in results
            ]
        }
