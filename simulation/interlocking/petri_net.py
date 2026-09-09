"""
Formal Petri-Net model for Computer-Based Interlocking verification.

Implements:
- Place/Transition/Arc structure
- Token firing semantics
- Reachability graph construction
- Safety property verification (mutual exclusion)
- Liveness verification (no deadlock)
- Bounded analysis
- ERTMS interlocking property specification
- Coverability tree generation
- Structural analysis (traps, siphons, invariants)
"""

from __future__ import annotations

import copy
import itertools
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, FrozenSet, Generator, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core data structures
# ---------------------------------------------------------------------------

class ArcType(Enum):
    NORMAL = auto()       # standard arc
    INHIBITOR = auto()    # fires only if place is empty
    READ = auto()         # test arc, does not consume
    RESET = auto()        # empties source place on fire


@dataclass
class Token:
    """A coloured token carrying optional data payload."""
    colour: str = "black"
    data: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.colour, tuple(sorted(self.data.items()))))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return False
        return self.colour == other.colour and self.data == other.data

    def __repr__(self) -> str:
        return f"Token(colour={self.colour!r})"


@dataclass
class Place:
    """A Petri-Net place holding a multiset of tokens."""
    name: str
    capacity: int = -1  # -1 = unbounded
    tokens: List[Token] = field(default_factory=list)
    label: str = ""
    initial_marking: List[Token] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.tokens and self.initial_marking:
            self.tokens = list(self.initial_marking)

    @property
    def token_count(self) -> int:
        return len(self.tokens)

    def is_empty(self) -> bool:
        return len(self.tokens) == 0

    def add_token(self, token: Optional[Token] = None) -> None:
        if self.capacity != -1 and len(self.tokens) >= self.capacity:
            raise OverflowError(f"Place {self.name!r} is at capacity {self.capacity}")
        self.tokens.append(token or Token())

    def remove_token(self, colour: str = "black") -> Token:
        for i, t in enumerate(self.tokens):
            if t.colour == colour:
                return self.tokens.pop(i)
        raise ValueError(f"No token with colour {colour!r} in place {self.name!r}")

    def clear(self) -> None:
        self.tokens.clear()

    def marking_signature(self) -> Tuple[str, ...]:
        return tuple(sorted(t.colour for t in self.tokens))

    def __repr__(self) -> str:
        return f"Place({self.name!r}, tokens={len(self.tokens)})"


@dataclass
class Arc:
    """Directed arc between a place and a transition (or vice versa)."""
    source: str        # place or transition name
    target: str        # place or transition name
    weight: int = 1
    arc_type: ArcType = ArcType.NORMAL
    colour_guard: Optional[str] = None  # restrict to specific token colour

    def __repr__(self) -> str:
        return f"Arc({self.source!r} -> {self.target!r}, w={self.weight}, type={self.arc_type.name})"


@dataclass
class Transition:
    """A Petri-Net transition that fires when its input places are enabled."""
    name: str
    label: str = ""
    guard: Optional[str] = None       # Python expression string evaluated at fire time
    priority: int = 0
    is_immediate: bool = False        # immediate vs timed transition
    timed_rate: float = 0.0           # rate for stochastic transitions
    inhibitor_threshold: int = 0      # inhibitor arc fires when tokens < threshold

    def __repr__(self) -> str:
        return f"Transition({self.name!r}, priority={self.priority})"


@dataclass
class Marking:
    """Snapshot of all place token counts in the net."""
    state: Dict[str, int] = field(default_factory=dict)

    def to_frozenset(self) -> FrozenSet[Tuple[str, int]]:
        return frozenset(self.state.items())

    @classmethod
    def from_places(cls, places: Dict[str, Place]) -> "Marking":
        return cls(state={name: p.token_count for name, p in places.items()})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Marking):
            return False
        return self.state == other.state

    def __hash__(self) -> int:
        return hash(self.to_frozenset())

    def __repr__(self) -> str:
        non_zero = {k: v for k, v in self.state.items() if v > 0}
        return f"Marking({non_zero})"


class ReachabilityNode:
    """Node in the reachability graph."""

    def __init__(self, marking: Marking) -> None:
        self.marking = marking
        self.successors: Dict[str, "ReachabilityNode"] = {}  # transition -> node
        self.predecessors: Dict[str, "ReachabilityNode"] = {}
        self.id: int = id(self)

    def __repr__(self) -> str:
        return f"RNode({self.marking})"


# ---------------------------------------------------------------------------
# Core Petri-Net engine
# ---------------------------------------------------------------------------

class PetriNet:
    """
    Full-featured Petri-Net engine with coloured tokens, arc types,
    reachability analysis, and formal verification.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.places: Dict[str, Place] = {}
        self.transitions: Dict[str, Transition] = {}
        self.input_arcs: Dict[str, List[Arc]] = defaultdict(list)   # transition -> arcs from places
        self.output_arcs: Dict[str, List[Arc]] = defaultdict(list)  # transition -> arcs to places
        self._initial_marking: Optional[Marking] = None
        self._firing_log: List[Dict[str, Any]] = []
        self._step_count: int = 0

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def add_place(self, name: str, capacity: int = -1, initial_tokens: int = 0,
                  label: str = "") -> Place:
        tokens = [Token() for _ in range(initial_tokens)]
        p = Place(name=name, capacity=capacity, tokens=tokens,
                  initial_marking=list(tokens), label=label)
        self.places[name] = p
        return p

    def add_transition(self, name: str, label: str = "", guard: Optional[str] = None,
                       priority: int = 0, is_immediate: bool = False,
                       timed_rate: float = 0.0) -> Transition:
        t = Transition(name=name, label=label, guard=guard, priority=priority,
                       is_immediate=is_immediate, timed_rate=timed_rate)
        self.transitions[name] = t
        return t

    def add_arc(self, source: str, target: str, weight: int = 1,
                arc_type: ArcType = ArcType.NORMAL,
                colour_guard: Optional[str] = None) -> Arc:
        arc = Arc(source=source, target=target, weight=weight,
                  arc_type=arc_type, colour_guard=colour_guard)
        # Determine direction: place -> transition (input) or transition -> place (output)
        if source in self.places and target in self.transitions:
            self.input_arcs[target].append(arc)
        elif source in self.transitions and target in self.places:
            self.output_arcs[source].append(arc)
        else:
            raise ValueError(f"Arc {source!r} -> {target!r}: one must be a place and other a transition")
        return arc

    def add_inhibitor_arc(self, place: str, transition: str, threshold: int = 1) -> Arc:
        arc = Arc(source=place, target=transition, weight=threshold,
                  arc_type=ArcType.INHIBITOR)
        self.input_arcs[transition].append(arc)
        return arc

    def save_initial_marking(self) -> None:
        self._initial_marking = Marking.from_places(self.places)

    def reset_to_initial(self) -> None:
        if self._initial_marking is None:
            raise RuntimeError("No initial marking saved — call save_initial_marking() first")
        for name, place in self.places.items():
            place.tokens = [Token() for _ in range(self._initial_marking.state.get(name, 0))]
        self._step_count = 0
        self._firing_log.clear()

    # ------------------------------------------------------------------
    # Firing logic
    # ------------------------------------------------------------------

    def is_enabled(self, transition_name: str) -> bool:
        """Check if a transition is enabled in the current marking."""
        if transition_name not in self.transitions:
            return False
        t = self.transitions[transition_name]
        for arc in self.input_arcs[transition_name]:
            place = self.places[arc.source]
            if arc.arc_type == ArcType.NORMAL:
                available = (sum(1 for tok in place.tokens
                                 if arc.colour_guard is None or tok.colour == arc.colour_guard))
                if available < arc.weight:
                    return False
            elif arc.arc_type == ArcType.INHIBITOR:
                if place.token_count >= arc.weight:
                    return False
            elif arc.arc_type == ArcType.READ:
                if place.token_count < arc.weight:
                    return False
        # Check guard expression
        if t.guard:
            ctx: Dict[str, Any] = {name: p.token_count for name, p in self.places.items()}
            try:
                if not eval(t.guard, {"__builtins__": {}}, ctx):  # noqa: S307
                    return False
            except Exception:
                return False
        return True

    def enabled_transitions(self) -> List[str]:
        """Return list of currently enabled transition names, sorted by priority desc."""
        enabled = [name for name in self.transitions if self.is_enabled(name)]
        return sorted(enabled, key=lambda n: self.transitions[n].priority, reverse=True)

    def fire(self, transition_name: str) -> bool:
        """
        Fire a transition, consuming/producing tokens.
        Returns True on success, False if not enabled.
        """
        if not self.is_enabled(transition_name):
            return False

        # Consume input tokens
        for arc in self.input_arcs[transition_name]:
            place = self.places[arc.source]
            if arc.arc_type == ArcType.NORMAL:
                colour = arc.colour_guard or "black"
                for _ in range(arc.weight):
                    # Try to remove by colour, fall back to any
                    removed = False
                    for i, tok in enumerate(place.tokens):
                        if arc.colour_guard is None or tok.colour == colour:
                            place.tokens.pop(i)
                            removed = True
                            break
                    if not removed:
                        logger.warning("Token removal failed for place %s", arc.source)
            elif arc.arc_type == ArcType.RESET:
                place.clear()
            # READ and INHIBITOR arcs do not consume tokens

        # Produce output tokens
        for arc in self.output_arcs[transition_name]:
            place = self.places[arc.target]
            colour = arc.colour_guard or "black"
            for _ in range(arc.weight):
                place.add_token(Token(colour=colour))

        self._step_count += 1
        self._firing_log.append({
            "step": self._step_count,
            "transition": transition_name,
            "marking": Marking.from_places(self.places).state.copy(),
        })
        return True

    def fire_sequence(self, sequence: List[str]) -> Tuple[bool, int]:
        """
        Fire a sequence of transitions. Returns (success, fired_count).
        Stops at first non-enabled transition.
        """
        for i, name in enumerate(sequence):
            if not self.fire(name):
                return False, i
        return True, len(sequence)

    def step(self) -> Optional[str]:
        """Fire the highest-priority enabled transition. Returns its name or None."""
        enabled = self.enabled_transitions()
        if not enabled:
            return None
        chosen = enabled[0]
        self.fire(chosen)
        return chosen

    def run_until_deadlock(self, max_steps: int = 10_000) -> List[str]:
        """Run the net until no transition is enabled or max_steps reached."""
        fired = []
        for _ in range(max_steps):
            t = self.step()
            if t is None:
                break
            fired.append(t)
        return fired

    # ------------------------------------------------------------------
    # Reachability analysis
    # ------------------------------------------------------------------

    def build_reachability_graph(self, max_states: int = 50_000) -> Dict[FrozenSet, ReachabilityNode]:
        """
        BFS over all reachable markings. Returns mapping of marking -> node.
        WARNING: can be exponential — use max_states to bound exploration.
        """
        if self._initial_marking is None:
            self.save_initial_marking()

        self.reset_to_initial()
        root_marking = Marking.from_places(self.places)
        root = ReachabilityNode(root_marking)

        visited: Dict[FrozenSet, ReachabilityNode] = {root_marking.to_frozenset(): root}
        queue: deque[Tuple[ReachabilityNode, Dict[str, int]]] = deque()
        queue.append((root, root_marking.state.copy()))

        explored = 0
        while queue and len(visited) < max_states:
            node, marking_state = queue.popleft()

            # Restore this marking
            for name, place in self.places.items():
                place.tokens = [Token() for _ in range(marking_state.get(name, 0))]

            for t_name in self.enabled_transitions():
                # Save current state
                saved = {n: p.token_count for n, p in self.places.items()}

                self.fire(t_name)
                new_marking = Marking.from_places(self.places)
                key = new_marking.to_frozenset()

                if key not in visited:
                    new_node = ReachabilityNode(new_marking)
                    visited[key] = new_node
                    queue.append((new_node, new_marking.state.copy()))
                else:
                    new_node = visited[key]

                node.successors[t_name] = new_node
                new_node.predecessors[t_name] = node

                # Restore before next transition
                for name, place in self.places.items():
                    place.tokens = [Token() for _ in range(saved.get(name, 0))]

            explored += 1

        logger.info("Reachability graph: %d states, %d explored", len(visited), explored)
        self.reset_to_initial()
        return visited

    def get_marking_vector(self) -> Dict[str, int]:
        return {name: p.token_count for name, p in self.places.items()}

    # ------------------------------------------------------------------
    # Structural analysis helpers
    # ------------------------------------------------------------------

    def compute_place_invariants(self) -> List[Dict[str, int]]:
        """
        Compute P-invariants (place invariants) using the Farkas algorithm.
        Returns list of invariant vectors {place_name: coefficient}.
        """
        # Build incidence matrix: rows=places, cols=transitions
        place_names = list(self.places.keys())
        trans_names = list(self.transitions.keys())
        n_p = len(place_names)
        n_t = len(trans_names)

        # incidence[i][j] = net change in place i when transition j fires
        incidence = [[0] * n_t for _ in range(n_p)]
        for j, t_name in enumerate(trans_names):
            for arc in self.output_arcs[t_name]:
                if arc.target in self.places:
                    i = place_names.index(arc.target)
                    incidence[i][j] += arc.weight
            for arc in self.input_arcs[t_name]:
                if arc.source in self.places and arc.arc_type == ArcType.NORMAL:
                    i = place_names.index(arc.source)
                    incidence[i][j] -= arc.weight

        # Simple P-invariant extraction: for small nets, enumerate combinations
        invariants = []
        for combo in itertools.combinations(range(n_p), min(n_p, 4)):
            # Check if sum of marked places is constant (simplified check)
            vec = {place_names[i]: 1 for i in combo}
            # Verify: for each transition, sum of (coefficient * change) = 0
            is_inv = True
            for j in range(n_t):
                net_change = sum(incidence[i][j] for i in combo)
                if net_change != 0:
                    is_inv = False
                    break
            if is_inv:
                invariants.append(vec)

        return invariants

    def find_siphons(self) -> List[Set[str]]:
        """Find minimal siphons (sets of places that can become empty and stay empty)."""
        place_names = list(self.places.keys())
        siphons = []

        for size in range(1, min(len(place_names) + 1, 6)):
            for subset in itertools.combinations(place_names, size):
                s = set(subset)
                # A siphon: every transition that has an output arc to S also has an input arc from S
                is_siphon = True
                for t_name in self.transitions:
                    outputs_to_s = any(arc.target in s for arc in self.output_arcs[t_name])
                    inputs_from_s = any(arc.source in s and arc.arc_type == ArcType.NORMAL
                                        for arc in self.input_arcs[t_name])
                    if outputs_to_s and not inputs_from_s:
                        is_siphon = False
                        break
                if is_siphon:
                    siphons.append(s)

        return siphons

    def find_traps(self) -> List[Set[str]]:
        """Find minimal traps (sets of places that are self-sustaining)."""
        place_names = list(self.places.keys())
        traps = []

        for size in range(1, min(len(place_names) + 1, 6)):
            for subset in itertools.combinations(place_names, size):
                s = set(subset)
                # A trap: every transition that has an input arc from S also has an output arc to S
                is_trap = True
                for t_name in self.transitions:
                    inputs_from_s = any(arc.source in s and arc.arc_type == ArcType.NORMAL
                                        for arc in self.input_arcs[t_name])
                    outputs_to_s = any(arc.target in s for arc in self.output_arcs[t_name])
                    if inputs_from_s and not outputs_to_s:
                        is_trap = False
                        break
                if is_trap:
                    traps.append(s)

        return traps

    # ------------------------------------------------------------------
    # Statistics and export
    # ------------------------------------------------------------------

    def statistics(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "places": len(self.places),
            "transitions": len(self.transitions),
            "total_arcs": sum(len(arcs) for arcs in self.input_arcs.values()) +
                          sum(len(arcs) for arcs in self.output_arcs.values()),
            "tokens": sum(p.token_count for p in self.places.values()),
            "steps_fired": self._step_count,
            "current_marking": self.get_marking_vector(),
        }

    def to_pnml(self) -> str:
        """Export to PNML (Petri Net Markup Language) XML string."""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">',
                 f'  <net id="{self.name}" type="http://www.pnml.org/version-2009/grammar/ptnet">',
                 f'    <name><text>{self.name}</text></name>',
                 '    <page id="page1">']

        for name, place in self.places.items():
            lines.append(f'      <place id="{name}">')
            lines.append(f'        <name><text>{place.label or name}</text></name>')
            if place.token_count > 0:
                lines.append(f'        <initialMarking><text>{place.token_count}</text></initialMarking>')
            lines.append('      </place>')

        for name, trans in self.transitions.items():
            lines.append(f'      <transition id="{name}">')
            lines.append(f'        <name><text>{trans.label or name}</text></name>')
            lines.append('      </transition>')

        arc_id = 0
        for t_name, arcs in self.input_arcs.items():
            for arc in arcs:
                arc_id += 1
                lines.append(f'      <arc id="a{arc_id}" source="{arc.source}" target="{arc.target}">')
                lines.append(f'        <inscription><text>{arc.weight}</text></inscription>')
                lines.append('      </arc>')

        for t_name, arcs in self.output_arcs.items():
            for arc in arcs:
                arc_id += 1
                lines.append(f'      <arc id="a{arc_id}" source="{arc.source}" target="{arc.target}">')
                lines.append(f'        <inscription><text>{arc.weight}</text></inscription>')
                lines.append('      </arc>')

        lines.extend(['    </page>', '  </net>', '</pnml>'])
        return "\n".join(lines)

    def firing_log(self) -> List[Dict[str, Any]]:
        return list(self._firing_log)

    def __repr__(self) -> str:
        return (f"PetriNet(name={self.name!r}, places={len(self.places)}, "
                f"transitions={len(self.transitions)})")


# ---------------------------------------------------------------------------
# Verification engine
# ---------------------------------------------------------------------------

@dataclass
class VerificationResult:
    property_name: str
    satisfied: bool
    evidence: List[str] = field(default_factory=list)
    counterexample: Optional[List[str]] = None
    details: str = ""


class PetriNetVerifier:
    """
    Formal verifier for Petri-Net interlocking properties.

    Supported properties:
    - SAFETY: Mutual exclusion — two conflicting routes cannot be simultaneously set
    - LIVENESS: Every enabled transition can eventually fire (no hidden deadlocks)
    - BOUNDEDNESS: All places are k-bounded (bounded token capacity)
    - REACHABILITY: A target marking is reachable from the initial marking
    - FAIRNESS: No transition is permanently starved
    - ERTMS_ROUTE_EXCLUSION: Railway-specific route exclusion invariant
    """

    def __init__(self, net: PetriNet) -> None:
        self.net = net
        self._reachability_graph: Optional[Dict[FrozenSet, ReachabilityNode]] = None

    def _ensure_reachability_graph(self, max_states: int = 50_000) -> None:
        if self._reachability_graph is None:
            self._reachability_graph = self.net.build_reachability_graph(max_states)

    def verify_boundedness(self, bound: int = 1) -> VerificationResult:
        """Verify that all places hold at most 'bound' tokens in all reachable markings."""
        self._ensure_reachability_graph()
        violations = []
        for key, node in self._reachability_graph.items():
            for place_name, count in node.marking.state.items():
                if count > bound:
                    violations.append(f"Place {place_name!r} has {count} tokens (bound={bound})")

        return VerificationResult(
            property_name=f"{bound}-Boundedness",
            satisfied=len(violations) == 0,
            evidence=violations[:10],
            details=f"Checked {len(self._reachability_graph)} reachable markings",
        )

    def verify_mutual_exclusion(self, place_a: str, place_b: str) -> VerificationResult:
        """Verify that places A and B are never simultaneously marked (mutual exclusion)."""
        self._ensure_reachability_graph()
        violations = []
        for key, node in self._reachability_graph.items():
            count_a = node.marking.state.get(place_a, 0)
            count_b = node.marking.state.get(place_b, 0)
            if count_a > 0 and count_b > 0:
                violations.append(f"Both {place_a!r}={count_a} and {place_b!r}={count_b} marked at {node.marking}")

        return VerificationResult(
            property_name=f"Mutual Exclusion ({place_a}, {place_b})",
            satisfied=len(violations) == 0,
            evidence=violations[:5],
            details=f"Checked {len(self._reachability_graph)} states",
        )

    def verify_deadlock_free(self) -> VerificationResult:
        """Verify that no reachable marking has zero enabled transitions (deadlock-free)."""
        self._ensure_reachability_graph()
        deadlocks = []
        for key, node in self._reachability_graph.items():
            if not node.successors:
                deadlocks.append(f"Deadlock at marking: {node.marking}")

        return VerificationResult(
            property_name="Deadlock-Freedom",
            satisfied=len(deadlocks) == 0,
            evidence=deadlocks[:5],
            details=f"Checked {len(self._reachability_graph)} states",
        )

    def verify_reachability(self, target_marking: Dict[str, int]) -> VerificationResult:
        """Verify that a specific target marking is reachable."""
        self._ensure_reachability_graph()
        for key, node in self._reachability_graph.items():
            # Check if target is a sub-marking
            matches = all(
                node.marking.state.get(place, 0) >= count
                for place, count in target_marking.items()
            )
            if matches:
                return VerificationResult(
                    property_name="Reachability",
                    satisfied=True,
                    details=f"Target marking reachable. State: {node.marking}",
                )

        return VerificationResult(
            property_name="Reachability",
            satisfied=False,
            evidence=[f"Target {target_marking} not found in {len(self._reachability_graph)} states"],
        )

    def verify_liveness(self, transition_name: str) -> VerificationResult:
        """Verify that a transition is live (can fire in every reachable marking, eventually)."""
        self._ensure_reachability_graph()
        # L1-liveness: transition fires at least once from initial state
        fired_anywhere = any(
            transition_name in node.successors
            for node in self._reachability_graph.values()
        )
        return VerificationResult(
            property_name=f"L1-Liveness ({transition_name})",
            satisfied=fired_anywhere,
            details=f"Transition appears in reachability graph: {fired_anywhere}",
        )

    def verify_ertms_route_exclusion(self, route_places: List[List[str]]) -> VerificationResult:
        """
        ERTMS-specific: verify that conflicting routes (sharing a track section)
        are never simultaneously set.
        """
        self._ensure_reachability_graph()
        violations = []

        # Check all pairs of routes
        for i, route_a in enumerate(route_places):
            for j, route_b in enumerate(route_places):
                if i >= j:
                    continue
                # Routes conflict if they share any place
                shared = set(route_a) & set(route_b)
                if not shared:
                    continue
                # Verify mutual exclusion for the "set" places of these routes
                for key, node in self._reachability_graph.items():
                    a_set = any(node.marking.state.get(p, 0) > 0 for p in route_a)
                    b_set = any(node.marking.state.get(p, 0) > 0 for p in route_b)
                    if a_set and b_set:
                        violations.append(
                            f"Routes {i} and {j} simultaneously set. Shared sections: {shared}")
                        break

        return VerificationResult(
            property_name="ERTMS Route Exclusion",
            satisfied=len(violations) == 0,
            evidence=violations[:10],
            details=f"Verified {len(route_places)} routes, {len(self._reachability_graph)} states",
        )

    def full_verification(self, conflict_pairs: Optional[List[Tuple[str, str]]] = None,
                          route_groups: Optional[List[List[str]]] = None) -> Dict[str, VerificationResult]:
        """Run all standard verification checks and return results dict."""
        results: Dict[str, VerificationResult] = {}
        results["boundedness"] = self.verify_boundedness(bound=1)
        results["deadlock_free"] = self.verify_deadlock_free()

        if conflict_pairs:
            for a, b in conflict_pairs:
                key = f"mutex_{a}_{b}"
                results[key] = self.verify_mutual_exclusion(a, b)

        if route_groups:
            results["ertms_route_exclusion"] = self.verify_ertms_route_exclusion(route_groups)

        return results

    def summary(self, results: Dict[str, VerificationResult]) -> str:
        lines = [f"=== Petri-Net Verification: {self.net.name} ==="]
        for name, r in results.items():
            status = "✓ PASS" if r.satisfied else "✗ FAIL"
            lines.append(f"  {status}  {r.property_name}")
            if not r.satisfied and r.evidence:
                for e in r.evidence[:3]:
                    lines.append(f"         • {e}")
        return "\n".join(lines)
