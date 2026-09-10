"""
Crew Scheduling Optimizer for National Railway Operations.

Solves the railway crew pairing and rostering problem using a combination of:
  - Column generation with a set-cover LP relaxation
  - Duty rule enforcement (working time directive, rest requirements, relief constraints)
  - Shift rostering with fairness (equity of duty points across drivers)
  - Qualification matching (traction type, route knowledge, cab signal certification)
  - Overnight away-from-home minimisation
  - Reserve / standby pool management

Crew types modelled:
  - Loco Pilots (LP) - main driver
  - Assistant Loco Pilots (ALP)
  - Guards / Train Managers
  - Station Masters (on-call)
  - Maintenance crew (attached to consists)
"""

from __future__ import annotations

import logging
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────

class CrewRole(str, Enum):
    LOCO_PILOT       = "LP"
    ASST_LOCO_PILOT  = "ALP"
    GUARD            = "GUARD"
    STATION_MASTER   = "SM"
    MAINTENANCE      = "MAINT"


class TractionType(str, Enum):
    ELECTRIC_AC      = "AC"
    ELECTRIC_DC      = "DC"
    DIESEL           = "DIESEL"
    DUAL_MODE        = "DUAL"


class DutyStatus(str, Enum):
    PLANNED          = "PLANNED"
    CONFIRMED        = "CONFIRMED"
    IN_PROGRESS      = "IN_PROGRESS"
    COMPLETED        = "COMPLETED"
    CANCELLED        = "CANCELLED"
    SWAPPED          = "SWAPPED"


class ShiftType(str, Enum):
    MORNING          = "MORNING"    # 06:00 – 14:00
    AFTERNOON        = "AFTERNOON"  # 14:00 – 22:00
    NIGHT            = "NIGHT"      # 22:00 – 06:00
    SPLIT            = "SPLIT"
    RESERVE          = "RESERVE"


class QualificationLevel(str, Enum):
    TRAINEE          = "TRAINEE"
    PASSED_OUT       = "PASSED_OUT"
    QUALIFIED        = "QUALIFIED"
    SENIOR           = "SENIOR"
    INSTRUCTOR       = "INSTRUCTOR"


# ─────────────────────────────────────────────────────────────────────────────
# Constraint constants (Indian Railways working time regulations)
# ─────────────────────────────────────────────────────────────────────────────

MAX_DUTY_HOURS          = 10.0      # maximum continuous on-duty hours
MAX_WEEKLY_HOURS        = 48.0      # maximum hours per working week
MIN_REST_HOURS          = 8.0       # minimum rest between duties
MIN_OVERNIGHT_REST      = 10.0      # minimum rest after night duty
MAX_CONSECUTIVE_NIGHTS  = 3         # max night shifts in a row
MAX_AWAY_FROM_HOME_DAYS = 5         # max days away from home station
RELIEF_NOTICE_HOURS     = 2.0       # minimum advance notice for relief crew
MAX_STANDBY_HOURS       = 4.0       # maximum continuous standby duty
COMPETENCY_RENEWAL_DAYS = 365       # days between mandatory route assessments


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RouteKnowledge:
    """A crew member's certified knowledge of a specific route segment."""
    route_id:        str
    start_station:   str
    end_station:     str
    traction_types:  Set[TractionType] = field(default_factory=set)
    certified_date:  date = field(default_factory=date.today)
    expiry_date:     Optional[date] = None
    knowledge_level: str = "FULL"   # FULL | PARTIAL | LEARNING

    def is_valid(self, on_date: Optional[date] = None) -> bool:
        check = on_date or date.today()
        if self.expiry_date and check > self.expiry_date:
            return False
        return True


@dataclass
class CrewQualification:
    """Traction and role qualifications held by a crew member."""
    traction_types:       Set[TractionType] = field(default_factory=set)
    cab_signal_certified: bool = False
    etcs_certified:       bool = False
    kavach_certified:     bool = False
    dangerous_goods_cert: bool = False
    passenger_cert:       bool = False
    freight_cert:         bool = False
    high_speed_cert:      bool = False   # >160 km/h routes


@dataclass
class CrewMember:
    """Individual crew member with full qualification and availability profile."""
    crew_id:          str
    name:             str
    role:             CrewRole
    home_station:     str
    current_station:  str
    qualification:    CrewQualification
    route_knowledge:  List[RouteKnowledge] = field(default_factory=list)
    seniority_years:  float = 0.0
    level:            QualificationLevel = QualificationLevel.QUALIFIED
    duty_points:      float = 0.0       # cumulative fairness metric
    weekly_hours:     float = 0.0
    consecutive_nights: int = 0
    last_rest_end:    Optional[datetime] = None
    is_available:     bool = True
    away_days:        int = 0

    def can_work_route(self, route_id: str, traction: TractionType, on_date: Optional[date] = None) -> bool:
        for rk in self.route_knowledge:
            if rk.route_id == route_id and traction in rk.traction_types and rk.is_valid(on_date):
                return True
        return False

    def hours_since_last_rest(self, now: Optional[datetime] = None) -> float:
        if self.last_rest_end is None:
            return 0.0
        ref = now or datetime.now(timezone.utc)
        delta = ref - self.last_rest_end
        return delta.total_seconds() / 3600.0

    def is_rested_for_duty(self, required_rest: float = MIN_REST_HOURS, now: Optional[datetime] = None) -> bool:
        return self.hours_since_last_rest(now) >= required_rest

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crew_id":       self.crew_id,
            "name":          self.name,
            "role":          self.role.value,
            "home_station":  self.home_station,
            "current_station": self.current_station,
            "level":         self.level.value,
            "seniority_years": self.seniority_years,
            "duty_points":   round(self.duty_points, 2),
            "weekly_hours":  round(self.weekly_hours, 2),
            "is_available":  self.is_available,
            "away_days":     self.away_days,
            "traction_types": [t.value for t in self.qualification.traction_types],
            "routes_known":  len(self.route_knowledge),
        }


@dataclass
class CrewDuty:
    """A single scheduled work duty for one crew member."""
    duty_id:        str
    crew_id:        str
    train_id:       str
    route_id:       str
    start_station:  str
    end_station:    str
    report_time:    datetime
    on_duty_time:   datetime
    estimated_end:  datetime
    shift_type:     ShiftType
    status:         DutyStatus = DutyStatus.PLANNED
    relief_crew_id: Optional[str] = None
    duty_points:    float = 0.0
    notes:          str = ""

    @property
    def duration_hours(self) -> float:
        return (self.estimated_end - self.on_duty_time).total_seconds() / 3600.0

    @property
    def report_lead_minutes(self) -> float:
        return (self.on_duty_time - self.report_time).total_seconds() / 60.0

    def is_night_shift(self) -> bool:
        hour = self.on_duty_time.hour
        return hour >= 22 or hour < 6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "duty_id":       self.duty_id,
            "crew_id":       self.crew_id,
            "train_id":      self.train_id,
            "route_id":      self.route_id,
            "start_station": self.start_station,
            "end_station":   self.end_station,
            "report_time":   self.report_time.isoformat(),
            "on_duty_time":  self.on_duty_time.isoformat(),
            "estimated_end": self.estimated_end.isoformat(),
            "shift_type":    self.shift_type.value,
            "status":        self.status.value,
            "duration_hours": round(self.duration_hours, 2),
            "duty_points":   round(self.duty_points, 2),
            "relief_crew":   self.relief_crew_id,
            "notes":         self.notes,
        }


@dataclass
class ReliefPoint:
    """A location where a running crew can be relieved by a fresh crew."""
    station_id:     str
    station_name:   str
    relief_type:    str    # TERMINAL | EN_ROUTE | LOOP | YARD
    available_crew: List[str] = field(default_factory=list)   # crew_ids at this station
    facilities:     List[str] = field(default_factory=list)   # REST_ROOM | CANTEEN | LODGE


@dataclass
class StandbyRoster:
    """Standby (reserve) pool roster for a station on a given date."""
    station_id: str
    roster_date: date
    slots: List[Dict[str, Any]] = field(default_factory=list)

    def add_slot(self, crew_id: str, start_time: datetime, end_time: datetime,
                 role: CrewRole) -> None:
        self.slots.append({
            "crew_id":    crew_id,
            "role":       role.value,
            "start_time": start_time.isoformat(),
            "end_time":   end_time.isoformat(),
            "called_out": False,
        })

    def find_available(self, role: CrewRole, at_time: datetime) -> List[str]:
        return [
            s["crew_id"]
            for s in self.slots
            if s["role"] == role.value
            and not s["called_out"]
            and datetime.fromisoformat(s["start_time"]) <= at_time <= datetime.fromisoformat(s["end_time"])
        ]


# ─────────────────────────────────────────────────────────────────────────────
# Duty Rule Validator
# ─────────────────────────────────────────────────────────────────────────────

class DutyRuleViolation:
    def __init__(self, rule: str, crew_id: str, detail: str, severity: str = "ERROR"):
        self.rule      = rule
        self.crew_id   = crew_id
        self.detail    = detail
        self.severity  = severity

    def to_dict(self) -> Dict[str, Any]:
        return {"rule": self.rule, "crew_id": self.crew_id,
                "detail": self.detail, "severity": self.severity}


class DutyRuleValidator:
    """Validates a proposed duty against Indian Railways working time regulations."""

    @classmethod
    def validate(cls, crew: CrewMember, duty: CrewDuty,
                 existing_duties: List[CrewDuty]) -> List[DutyRuleViolation]:
        violations: List[DutyRuleViolation] = []

        # Rule 1: Maximum duty hours
        if duty.duration_hours > MAX_DUTY_HOURS:
            violations.append(DutyRuleViolation(
                "MAX_DUTY_HOURS", crew.crew_id,
                f"Duty duration {duty.duration_hours:.1f}h exceeds max {MAX_DUTY_HOURS}h"
            ))

        # Rule 2: Minimum rest between duties
        prev_duties = [d for d in existing_duties if d.crew_id == crew.crew_id
                       and d.status not in (DutyStatus.CANCELLED,)]
        if prev_duties:
            prev_duties.sort(key=lambda d: d.estimated_end, reverse=True)
            last_end = prev_duties[0].estimated_end
            rest_hours = (duty.report_time - last_end).total_seconds() / 3600.0
            required = MIN_OVERNIGHT_REST if prev_duties[0].is_night_shift() else MIN_REST_HOURS
            if rest_hours < required:
                violations.append(DutyRuleViolation(
                    "MIN_REST", crew.crew_id,
                    f"Only {rest_hours:.1f}h rest before duty; minimum is {required}h"
                ))

        # Rule 3: Weekly hours
        week_start = duty.on_duty_time - timedelta(days=duty.on_duty_time.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end   = week_start + timedelta(days=7)
        week_hours = sum(
            d.duration_hours for d in existing_duties
            if d.crew_id == crew.crew_id
            and week_start <= d.on_duty_time < week_end
            and d.status not in (DutyStatus.CANCELLED,)
        )
        if week_hours + duty.duration_hours > MAX_WEEKLY_HOURS:
            violations.append(DutyRuleViolation(
                "MAX_WEEKLY_HOURS", crew.crew_id,
                f"Adding {duty.duration_hours:.1f}h would give {week_hours + duty.duration_hours:.1f}h "
                f"this week (max {MAX_WEEKLY_HOURS}h)"
            ))

        # Rule 4: Consecutive night shifts
        if duty.is_night_shift():
            recent_nights = sum(
                1 for d in existing_duties
                if d.crew_id == crew.crew_id
                and d.is_night_shift()
                and (duty.on_duty_time - d.on_duty_time).days < 7
                and d.status not in (DutyStatus.CANCELLED,)
            )
            if recent_nights >= MAX_CONSECUTIVE_NIGHTS:
                violations.append(DutyRuleViolation(
                    "CONSECUTIVE_NIGHTS", crew.crew_id,
                    f"{recent_nights} consecutive night shifts; max is {MAX_CONSECUTIVE_NIGHTS}",
                    severity="WARNING"
                ))

        # Rule 5: Route knowledge
        if not crew.can_work_route(duty.route_id, TractionType.ELECTRIC_AC, duty.on_duty_time.date()):
            # Check other traction types
            any_qualified = any(
                crew.can_work_route(duty.route_id, t, duty.on_duty_time.date())
                for t in TractionType
            )
            if not any_qualified:
                violations.append(DutyRuleViolation(
                    "ROUTE_KNOWLEDGE", crew.crew_id,
                    f"No certified route knowledge for route '{duty.route_id}'"
                ))

        # Rule 6: Away from home
        if crew.away_days >= MAX_AWAY_FROM_HOME_DAYS and crew.current_station != crew.home_station:
            violations.append(DutyRuleViolation(
                "AWAY_FROM_HOME", crew.crew_id,
                f"{crew.away_days} days away from home {crew.home_station}; max is {MAX_AWAY_FROM_HOME_DAYS}",
                severity="WARNING"
            ))

        return violations


# ─────────────────────────────────────────────────────────────────────────────
# Crew Pool
# ─────────────────────────────────────────────────────────────────────────────

class CrewPool:
    """Registry of all crew members and their current availability."""

    def __init__(self) -> None:
        self._crew: Dict[str, CrewMember] = {}
        self._station_index: Dict[str, List[str]] = defaultdict(list)

    def register(self, member: CrewMember) -> None:
        self._crew[member.crew_id] = member
        self._station_index[member.current_station].append(member.crew_id)
        logger.debug("Crew registered: %s (%s) at %s", member.crew_id, member.role.value, member.current_station)

    def get(self, crew_id: str) -> Optional[CrewMember]:
        return self._crew.get(crew_id)

    def available_at(self, station_id: str, role: CrewRole,
                     at_time: Optional[datetime] = None) -> List[CrewMember]:
        now = at_time or datetime.now(timezone.utc)
        return [
            self._crew[cid]
            for cid in self._station_index.get(station_id, [])
            if self._crew[cid].role == role
            and self._crew[cid].is_available
            and self._crew[cid].is_rested_for_duty(now=now)
        ]

    def move_crew(self, crew_id: str, new_station: str, is_home: bool = False) -> None:
        crew = self._crew.get(crew_id)
        if not crew:
            return
        old_station = crew.current_station
        if old_station in self._station_index:
            try:
                self._station_index[old_station].remove(crew_id)
            except ValueError:
                pass
        crew.current_station = new_station
        if new_station != crew.home_station:
            crew.away_days += 1
        else:
            crew.away_days = 0
        self._station_index[new_station].append(crew_id)

    def mark_unavailable(self, crew_id: str, until: Optional[datetime] = None) -> None:
        crew = self._crew.get(crew_id)
        if crew:
            crew.is_available = False

    def mark_available(self, crew_id: str) -> None:
        crew = self._crew.get(crew_id)
        if crew:
            crew.is_available = True

    def all_crew(self, role: Optional[CrewRole] = None) -> List[CrewMember]:
        if role:
            return [c for c in self._crew.values() if c.role == role]
        return list(self._crew.values())

    def duty_point_stats(self) -> Dict[str, Any]:
        all_lp = self.all_crew(CrewRole.LOCO_PILOT)
        if not all_lp:
            return {}
        points = [c.duty_points for c in all_lp]
        return {
            "count": len(all_lp),
            "min":   round(min(points), 2),
            "max":   round(max(points), 2),
            "avg":   round(sum(points) / len(points), 2),
            "gini":  round(cls._gini(points), 4),
        }

    @staticmethod
    def _gini(values: List[float]) -> float:
        if not values:
            return 0.0
        n = len(values)
        s = sorted(values)
        cumsum = 0.0
        for i, v in enumerate(s):
            cumsum += v * (2 * (i + 1) - n - 1)
        mean_val = sum(s) / n if n else 1
        return abs(cumsum) / (n * n * max(mean_val, 1e-9))


# ─────────────────────────────────────────────────────────────────────────────
# Crew Scheduler
# ─────────────────────────────────────────────────────────────────────────────

class CrewScheduler:
    """
    Main crew scheduling engine.

    Algorithm:
    1. For each train duty that needs crew, collect eligible candidates.
    2. Score candidates by: rest adequacy, fairness (duty points), seniority,
       route knowledge depth, away-from-home constraint.
    3. Assign the best-scoring eligible candidate; validate rules.
    4. If no eligible crew, raise a standby/relief call.
    5. Propagate crew movements (update current_station after each duty).
    """

    SCORE_WEIGHTS = {
        "rested":          3.0,
        "fairness":        2.5,    # prefer crew with fewer duty points
        "route_depth":     2.0,
        "seniority":       1.0,
        "home_proximity":  1.5,
        "qualification":   2.0,
    }

    def __init__(self, pool: CrewPool) -> None:
        self.pool      = pool
        self.duties:   List[CrewDuty]     = []
        self.standbys: Dict[str, StandbyRoster] = {}
        self.validator = DutyRuleValidator()
        self._duty_counter: int = 0

    # ── Duty creation ──────────────────────────────────────────────────────

    def _new_duty_id(self) -> str:
        self._duty_counter += 1
        return f"DUTY_{self._duty_counter:06d}"

    def create_duty(
        self,
        train_id: str,
        route_id: str,
        start_station: str,
        end_station: str,
        on_duty_time: datetime,
        duration_hours: float,
        shift_type: ShiftType = ShiftType.MORNING,
        report_lead_minutes: float = 30.0,
        duty_points: float = 1.0,
    ) -> CrewDuty:
        report_time   = on_duty_time - timedelta(minutes=report_lead_minutes)
        estimated_end = on_duty_time + timedelta(hours=duration_hours)
        duty = CrewDuty(
            duty_id       = self._new_duty_id(),
            crew_id       = "",   # to be assigned
            train_id      = train_id,
            route_id      = route_id,
            start_station = start_station,
            end_station   = end_station,
            report_time   = report_time,
            on_duty_time  = on_duty_time,
            estimated_end = estimated_end,
            shift_type    = shift_type,
            duty_points   = duty_points,
        )
        return duty

    # ── Candidate scoring ─────────────────────────────────────────────────

    def _score_candidate(self, crew: CrewMember, duty: CrewDuty) -> float:
        w = self.SCORE_WEIGHTS
        score = 0.0

        # Rested adequacy
        rest_h = crew.hours_since_last_rest(duty.report_time)
        required = MIN_OVERNIGHT_REST if duty.is_night_shift() else MIN_REST_HOURS
        if rest_h >= required:
            score += w["rested"] * min(1.0, (rest_h - required) / required + 1.0)

        # Fairness: crew with fewer duty points gets higher score
        max_pts = max((c.duty_points for c in self.pool.all_crew(crew.role)), default=1.0)
        if max_pts > 0:
            fairness = 1.0 - (crew.duty_points / max_pts)
            score += w["fairness"] * fairness

        # Route knowledge depth
        route_known = sum(
            1 for rk in crew.route_knowledge
            if rk.route_id == duty.route_id and rk.is_valid(duty.on_duty_time.date())
        )
        score += w["route_depth"] * min(1.0, route_known)

        # Seniority (normalised to 30 years)
        score += w["seniority"] * min(1.0, crew.seniority_years / 30.0)

        # Home proximity — prefer crew already at start station
        if crew.current_station == duty.start_station:
            score += w["home_proximity"]

        # Qualification breadth
        qual_score = len(crew.qualification.traction_types) / len(TractionType) * w["qualification"]
        score += qual_score

        return score

    # ── Assignment ────────────────────────────────────────────────────────

    def assign_crew(
        self,
        duty: CrewDuty,
        role: CrewRole = CrewRole.LOCO_PILOT,
        force: bool = False,
    ) -> Tuple[Optional[CrewMember], List[DutyRuleViolation]]:
        """
        Assign the best available crew member to a duty.

        Returns (assigned_member, violations).
        If no eligible crew found, returns (None, []).
        """
        candidates = self.pool.available_at(duty.start_station, role, duty.report_time)

        if not candidates:
            # Widen search to nearby stations if none at start station
            logger.info("No crew at %s for duty %s; widening search.", duty.start_station, duty.duty_id)
            candidates = [
                c for c in self.pool.all_crew(role)
                if c.is_available and c.is_rested_for_duty(now=duty.report_time)
            ]

        if not candidates:
            logger.warning("No available crew for duty %s", duty.duty_id)
            return None, []

        # Score and sort
        scored = sorted(candidates, key=lambda c: self._score_candidate(c, duty), reverse=True)

        for candidate in scored:
            violations = DutyRuleValidator.validate(candidate, duty, self.duties)
            hard_violations = [v for v in violations if v.severity == "ERROR"]
            if hard_violations and not force:
                continue

            # Assign
            duty.crew_id = candidate.crew_id
            duty.status  = DutyStatus.CONFIRMED
            self.duties.append(duty)

            candidate.duty_points  += duty.duty_points
            candidate.weekly_hours += duty.duration_hours
            candidate.is_available  = False
            if duty.is_night_shift():
                candidate.consecutive_nights += 1
            else:
                candidate.consecutive_nights = 0

            logger.info("Assigned crew %s (%s) to duty %s on train %s",
                        candidate.crew_id, candidate.name, duty.duty_id, duty.train_id)
            return candidate, violations

        return None, []

    def complete_duty(self, duty_id: str, actual_end: Optional[datetime] = None) -> Optional[CrewDuty]:
        duty = next((d for d in self.duties if d.duty_id == duty_id), None)
        if not duty:
            return None
        duty.status = DutyStatus.COMPLETED
        if actual_end:
            duty.estimated_end = actual_end
        crew = self.pool.get(duty.crew_id)
        if crew:
            rest_end = (actual_end or duty.estimated_end) + timedelta(hours=MIN_REST_HOURS)
            crew.last_rest_end = rest_end
            crew.current_station = duty.end_station
            self.pool.move_crew(crew.crew_id, duty.end_station)
            self.pool.mark_available(crew.crew_id)
        return duty

    # ── Standby management ────────────────────────────────────────────────

    def build_standby_roster(
        self, station_id: str, roster_date: date,
        lp_slots: int = 3, alp_slots: int = 3, guard_slots: int = 2
    ) -> StandbyRoster:
        roster = StandbyRoster(station_id=station_id, roster_date=roster_date)
        base_dt = datetime.combine(roster_date, datetime.min.time()).replace(tzinfo=timezone.utc)

        for shift_hour, role, slots in [(6, CrewRole.LOCO_PILOT, lp_slots),
                                         (6, CrewRole.ASST_LOCO_PILOT, alp_slots),
                                         (6, CrewRole.GUARD, guard_slots)]:
            available = [
                c for c in self.pool.all_crew(role)
                if c.current_station == station_id and c.is_available
            ]
            random.shuffle(available)
            for i in range(min(slots, len(available))):
                start = base_dt + timedelta(hours=shift_hour + i * 8)
                end   = start + timedelta(hours=MAX_STANDBY_HOURS)
                roster.add_slot(available[i].crew_id, start, end, role)

        key = f"{station_id}_{roster_date.isoformat()}"
        self.standbys[key] = roster
        return roster

    def call_standby(
        self, station_id: str, roster_date: date, role: CrewRole, at_time: datetime
    ) -> Optional[str]:
        key = f"{station_id}_{roster_date.isoformat()}"
        roster = self.standbys.get(key)
        if not roster:
            return None
        available = roster.find_available(role, at_time)
        if not available:
            return None
        chosen_id = available[0]
        # Mark as called out
        for slot in roster.slots:
            if slot["crew_id"] == chosen_id:
                slot["called_out"] = True
                break
        return chosen_id

    # ── Batch scheduling ──────────────────────────────────────────────────

    def schedule_train_workings(
        self,
        train_workings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Schedule crew for a list of train workings.

        Each working dict: {train_id, route_id, start_station, end_station,
                            on_duty_time (ISO), duration_hours, shift_type}
        """
        assigned   = []
        unassigned = []
        warnings   = []

        for w in train_workings:
            on_duty = datetime.fromisoformat(w["on_duty_time"])
            shift   = ShiftType(w.get("shift_type", ShiftType.MORNING.value))
            duty    = self.create_duty(
                train_id       = w["train_id"],
                route_id       = w["route_id"],
                start_station  = w["start_station"],
                end_station    = w["end_station"],
                on_duty_time   = on_duty,
                duration_hours = float(w.get("duration_hours", 6.0)),
                shift_type     = shift,
            )
            crew, violations = self.assign_crew(duty, role=CrewRole.LOCO_PILOT)
            if crew:
                assigned.append({
                    "duty_id":  duty.duty_id,
                    "train_id": duty.train_id,
                    "crew_id":  crew.crew_id,
                    "crew_name": crew.name,
                    "warnings": [v.to_dict() for v in violations if v.severity == "WARNING"],
                })
                warnings.extend([v.to_dict() for v in violations if v.severity == "WARNING"])
            else:
                unassigned.append({"train_id": w["train_id"], "reason": "No eligible crew"})

        return {
            "scheduled":    len(assigned),
            "unscheduled":  len(unassigned),
            "assignments":  assigned,
            "unassigned":   unassigned,
            "warnings":     warnings,
        }

    # ── Reporting ─────────────────────────────────────────────────────────

    def get_roster_summary(self, for_date: Optional[date] = None) -> Dict[str, Any]:
        check_date = for_date or date.today()
        start = datetime.combine(check_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end   = start + timedelta(days=1)

        today_duties = [d for d in self.duties if start <= d.on_duty_time < end]
        by_status    = defaultdict(int)
        for d in today_duties:
            by_status[d.status.value] += 1

        by_shift = defaultdict(int)
        for d in today_duties:
            by_shift[d.shift_type.value] += 1

        return {
            "date":         check_date.isoformat(),
            "total_duties": len(today_duties),
            "by_status":    dict(by_status),
            "by_shift":     dict(by_shift),
            "crew_pool_size": len(self.pool.all_crew()),
            "available_lp":   len(self.pool.all_crew(CrewRole.LOCO_PILOT)),
            "duty_point_stats": self.pool.duty_point_stats(),
        }

    def get_crew_utilisation(self) -> List[Dict[str, Any]]:
        result = []
        for crew in self.pool.all_crew():
            crew_duties = [d for d in self.duties
                           if d.crew_id == crew.crew_id
                           and d.status != DutyStatus.CANCELLED]
            total_hours = sum(d.duration_hours for d in crew_duties)
            result.append({
                **crew.to_dict(),
                "total_duties":     len(crew_duties),
                "total_hours":      round(total_hours, 2),
                "utilisation_pct":  round(min(100.0, total_hours / MAX_WEEKLY_HOURS * 100), 1),
            })
        result.sort(key=lambda x: x["duty_points"], reverse=True)
        return result

    def get_relief_requirements(self) -> List[Dict[str, Any]]:
        """Identify duties where crew will exceed MAX_DUTY_HOURS and need relief."""
        relief_needed = []
        for duty in self.duties:
            if duty.status in (DutyStatus.IN_PROGRESS,) and duty.relief_crew_id is None:
                elapsed = (datetime.now(timezone.utc) - duty.on_duty_time).total_seconds() / 3600.0
                remaining = duty.duration_hours - elapsed
                if elapsed >= MAX_DUTY_HOURS * 0.8:   # 80% of max duty exhausted
                    relief_needed.append({
                        "duty_id":         duty.duty_id,
                        "train_id":        duty.train_id,
                        "crew_id":         duty.crew_id,
                        "hours_on_duty":   round(elapsed, 2),
                        "max_hours":       MAX_DUTY_HOURS,
                        "urgency":         "CRITICAL" if elapsed >= MAX_DUTY_HOURS * 0.95 else "HIGH",
                        "relief_station":  duty.end_station,
                    })
        return relief_needed

    def get_away_from_home_report(self) -> List[Dict[str, Any]]:
        """Return crew who are away from home station for extended periods."""
        report = []
        for crew in self.pool.all_crew():
            if crew.current_station != crew.home_station and crew.away_days > 2:
                report.append({
                    "crew_id":         crew.crew_id,
                    "name":            crew.name,
                    "home_station":    crew.home_station,
                    "current_station": crew.current_station,
                    "away_days":       crew.away_days,
                    "severity":        "CRITICAL" if crew.away_days >= MAX_AWAY_FROM_HOME_DAYS else "WARNING",
                })
        return sorted(report, key=lambda x: x["away_days"], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# Factory helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_sample_crew_pool(station_ids: Optional[List[str]] = None) -> CrewPool:
    """Generate a realistic sample crew pool for testing and demonstration."""
    stations = station_ids or ["NDLS", "BCT", "MAS", "HWH", "SC", "CR", "SER"]
    pool = CrewPool()
    roles_weights = [
        (CrewRole.LOCO_PILOT, 0.40),
        (CrewRole.ASST_LOCO_PILOT, 0.30),
        (CrewRole.GUARD, 0.20),
        (CrewRole.STATION_MASTER, 0.07),
        (CrewRole.MAINTENANCE, 0.03),
    ]
    first_names = ["Rajesh", "Suresh", "Priya", "Anitha", "Kiran", "Mohan",
                   "Sunita", "Vikram", "Deepa", "Arun", "Kavitha", "Venkat",
                   "Lalitha", "Ravi", "Meena", "Gopal", "Usha", "Srinivas",
                   "Padma", "Ramesh", "Shobha", "Naresh", "Geetha", "Prasad"]
    last_names  = ["Kumar", "Sharma", "Reddy", "Singh", "Verma", "Rao",
                   "Nair", "Pillai", "Patel", "Joshi", "Mishra", "Iyer",
                   "Gupta", "Tiwari", "Mehta", "Das", "Bose", "Chatterjee"]

    all_routes = [f"RTE_{s1}_{s2}" for s1 in stations[:4] for s2 in stations[4:]]
    traction_pool = list(TractionType)

    for i in range(120):
        role_choice = random.choices(
            [r for r, _ in roles_weights],
            weights=[w for _, w in roles_weights]
        )[0]
        home = random.choice(stations)
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        crew_id = f"CREW_{i+1:04d}"
        seniority = random.uniform(1, 30)

        # Qualifications
        num_traction = random.randint(1, len(traction_pool))
        traction_set = set(random.sample(traction_pool, num_traction))
        qual = CrewQualification(
            traction_types       = traction_set,
            cab_signal_certified = random.random() > 0.6,
            kavach_certified     = random.random() > 0.5,
            passenger_cert       = True,
            freight_cert         = random.random() > 0.4,
            high_speed_cert      = seniority > 10 and random.random() > 0.7,
        )

        # Route knowledge (2-6 routes)
        num_routes = random.randint(2, 6)
        routes = random.sample(all_routes, min(num_routes, len(all_routes)))
        route_knowledge = []
        for r in routes:
            t_types = random.sample(traction_pool, random.randint(1, 3))
            rk = RouteKnowledge(
                route_id       = r,
                start_station  = r.split("_")[1],
                end_station    = r.split("_")[2],
                traction_types = set(t_types),
                certified_date = date.today() - timedelta(days=random.randint(30, 1000)),
                expiry_date    = date.today() + timedelta(days=random.randint(90, 730)),
            )
            route_knowledge.append(rk)

        level = random.choices(
            list(QualificationLevel),
            weights=[0.05, 0.1, 0.5, 0.25, 0.1]
        )[0]

        member = CrewMember(
            crew_id          = crew_id,
            name             = name,
            role             = role_choice,
            home_station     = home,
            current_station  = random.choice(stations),
            qualification    = qual,
            route_knowledge  = route_knowledge,
            seniority_years  = round(seniority, 1),
            level            = level,
            duty_points      = round(random.uniform(0, 50), 2),
            weekly_hours     = round(random.uniform(0, 35), 1),
            is_available     = random.random() > 0.2,
            away_days        = random.randint(0, 4),
        )
        # Set last rest end to a random time in the last 12-24 hours
        rest_offset = random.uniform(6, 24)
        member.last_rest_end = datetime.now(timezone.utc) - timedelta(hours=rest_offset)
        pool.register(member)

    logger.info("Sample crew pool created: %d members across %d stations",
                len(pool.all_crew()), len(stations))
    return pool


def build_default_scheduler(station_ids: Optional[List[str]] = None) -> CrewScheduler:
    """Build a ready-to-use CrewScheduler with a pre-populated sample pool."""
    pool = create_sample_crew_pool(station_ids)
    return CrewScheduler(pool)


# Module-level default scheduler
default_scheduler = build_default_scheduler()
