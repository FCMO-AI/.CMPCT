"""CMPCT v0.30 child research — bounded Representation Superoptimizer extractor.

The compressor is accumulating several *equivalent* ways to reconstruct the same logical bytes: direct/GIR,
Mosaic or PrefixGraph edges, synthetic phrase atoms, latent sequence programs and binary transforms.  Choosing
one class destructively before another creates phase-ordering risk.

This module does not implement a general e-graph.  It models the part CMPCT actually needs: each logical target
keeps a bounded set of byte-exact plans; some plans require shared facilities (materialized roots, synthetic
atoms, dictionaries); facilities pay their stored opening cost once; and a bounded global extractor chooses the
cheapest legal closure.

The optimization resembles facility-location/set-cover and equality-saturation extraction, neither of which is
claimed as novel.  The CMPCT research contribution under test is the archive-specific typed frontier and cost
surface: complete stored bytes plus hard locality/depth/memory/parser certificates, eventually extended with
recovery fan-out and timing debt.

Production hardening adds one important proof strategy: the target/facility graph is decomposed into independent
connected components.  Components with <=18 active facilities are solved exhaustively, so a large archive can
still receive a *global optimality certificate* when sharing is locally sparse.  Oversized components fall back
to the bounded beam and are explicitly reported as unproven rather than being presented as optimal.

Footnote: all numbers accepted by this core are already-computed *complete local costs*.  It never estimates
compression ratio from entropy or file type.  Representation generators remain responsible for exact inverse
proofs and descriptor/framing charges before a Plan reaches this extractor.  The optimizer is also forbidden
from dropping a target merely because all of its clever plans violated policy: every declared target must retain
one legal facility-free fallback or construction fails closed.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from typing import Iterable

MAX_REQUIREMENTS_PER_PLAN = 4
DEFAULT_BEAM_WIDTH = 64
DEFAULT_MAX_ROUNDS = 16
DEFAULT_MAX_EXPANSIONS = 20_000
MAX_EXACT_FACILITIES = 18


def _plain_int(value, label: str) -> int:
    if type(value) is not int:  # bool is deliberately excluded despite being an int subclass.
        raise ValueError(f"{label} must be an integer byte/resource count")
    return value


@dataclass(frozen=True, slots=True)
class Policy:
    """Hard representation boundary applied before any size optimization."""

    max_dependency_depth: int = 1
    max_read_amplification: float = 8.0
    max_peak_memory_bytes: int = 512 * 1024 * 1024
    max_parser_risk: int = 3

    def __post_init__(self) -> None:
        _plain_int(self.max_dependency_depth, "policy dependency depth")
        _plain_int(self.max_peak_memory_bytes, "policy peak memory")
        _plain_int(self.max_parser_risk, "policy parser risk")
        if self.max_dependency_depth < 0 or self.max_peak_memory_bytes < 0 or self.max_parser_risk < 0:
            raise ValueError("negative representation policy bound")
        if not math.isfinite(float(self.max_read_amplification)) or self.max_read_amplification < 0:
            raise ValueError("invalid representation read-amplification policy")


@dataclass(frozen=True, slots=True)
class Facility:
    facility_id: str
    opening_bytes: int
    kind: str = "shared-basis"

    def __post_init__(self) -> None:
        _plain_int(self.opening_bytes, "facility opening bytes")
        if not self.facility_id or not self.kind or self.opening_bytes < 0:
            raise ValueError("invalid representation facility")


@dataclass(frozen=True, slots=True)
class Plan:
    target_id: str
    plan_id: str
    private_bytes: int
    requires: frozenset[str] = frozenset()
    dependency_depth: int = 0
    read_amplification: float = 1.0
    peak_memory_bytes: int = 0
    parser_risk: int = 0
    representation_kind: str = "direct"

    def __post_init__(self) -> None:
        _plain_int(self.private_bytes, "plan private bytes")
        _plain_int(self.dependency_depth, "plan dependency depth")
        _plain_int(self.peak_memory_bytes, "plan peak memory")
        _plain_int(self.parser_risk, "plan parser risk")
        if not self.target_id or not self.plan_id or not self.representation_kind or self.private_bytes < 0:
            raise ValueError("invalid representation plan")
        if not isinstance(self.requires, frozenset) or any(not isinstance(value, str) or not value for value in self.requires):
            raise ValueError("representation plan requirements must be a frozenset of non-empty facility ids")
        if len(self.requires) > MAX_REQUIREMENTS_PER_PLAN:
            raise ValueError("representation plan exceeds shared-requirement ceiling")
        if self.dependency_depth < 0 or self.peak_memory_bytes < 0 or self.parser_risk < 0:
            raise ValueError("negative representation resource declaration")
        if not math.isfinite(float(self.read_amplification)) or self.read_amplification < 0:
            raise ValueError("invalid representation read-amplification declaration")


@dataclass(frozen=True, slots=True)
class Extraction:
    total_bytes: int
    facility_bytes: int
    private_bytes: int
    opened: frozenset[str]
    selected: tuple[Plan, ...]
    method: str
    states_evaluated: int


class Problem:
    def __init__(self, facilities: Iterable[Facility], plans: Iterable[Plan], policy: Policy = Policy()):
        facility_rows = list(facilities)
        plan_rows = list(plans)
        self.facilities = {row.facility_id: row for row in facility_rows}
        if len(self.facilities) != len(facility_rows):
            raise ValueError("duplicate representation facility id")
        self.policy = policy
        if not plan_rows:
            raise ValueError("representation problem has no declared plans")

        declared_targets = {plan.target_id for plan in plan_rows}
        plan_keys = [(plan.target_id, plan.plan_id) for plan in plan_rows]
        if len(set(plan_keys)) != len(plan_keys):
            raise ValueError("duplicate representation plan identity")

        legal: list[Plan] = []
        known = set(self.facilities)
        for plan in plan_rows:
            if not plan.requires <= known:
                raise ValueError(f"plan {plan.plan_id} references unknown facility")
            if self._legal(plan):
                legal.append(plan)

        by_target: dict[str, list[Plan]] = {}
        for plan in legal:
            by_target.setdefault(plan.target_id, []).append(plan)

        # Footnote: this check is intentionally against the *declared* target set, not merely targets that
        # survived the policy filter.  The earlier research draft could silently omit a target whose every plan
        # was illegal, producing an apparently tiny extraction that did not reconstruct the whole problem.
        missing = sorted(declared_targets - set(by_target))
        if missing:
            raise ValueError(f"representation target has no legal plan after policy filtering: {missing[0]}")
        for target in sorted(declared_targets):
            rows = by_target[target]
            if not any(not row.requires for row in rows):
                raise ValueError(f"target {target} lacks a legal facility-free fallback")
            rows.sort(key=self._plan_rank)
        self.by_target = {target: by_target[target] for target in sorted(declared_targets)}
        self.declared_targets = frozenset(declared_targets)

        bundles = {plan.requires for rows in self.by_target.values() for plan in rows if plan.requires}
        # Opening a candidate's full requirement bundle in one transition is essential for Mosaic-like plans:
        # neither of two roots may be useful alone even though the pair is globally profitable.
        self.bundles = tuple(sorted(bundles, key=lambda bundle: (len(bundle), tuple(sorted(bundle)))))
        self.active_facilities = frozenset().union(*(self.bundles or (frozenset(),)))

    def _legal(self, plan: Plan) -> bool:
        p = self.policy
        return (
            plan.dependency_depth <= p.max_dependency_depth
            and plan.read_amplification <= p.max_read_amplification
            and plan.peak_memory_bytes <= p.max_peak_memory_bytes
            and plan.parser_risk <= p.max_parser_risk
        )

    @staticmethod
    def _plan_rank(plan: Plan) -> tuple:
        return (
            plan.private_bytes,
            plan.dependency_depth,
            plan.read_amplification,
            plan.peak_memory_bytes,
            plan.parser_risk,
            plan.representation_kind,
            plan.plan_id,
        )

    def evaluate(self, opened: frozenset[str]) -> Extraction:
        if not isinstance(opened, frozenset) or not opened <= self.facilities.keys():
            raise ValueError("unknown or non-canonical opened facility set")
        selected: list[Plan] = []
        private = 0
        for target, rows in self.by_target.items():
            feasible = [plan for plan in rows if plan.requires <= opened]
            if not feasible:
                raise RuntimeError(f"representation target lost its facility-free fallback: {target}")
            winner = min(feasible, key=self._plan_rank)
            selected.append(winner)
            private += winner.private_bytes
        if {plan.target_id for plan in selected} != set(self.declared_targets) or len(selected) != len(self.declared_targets):
            raise RuntimeError("representation extraction did not cover every declared target exactly once")
        facility_bytes = sum(self.facilities[facility_id].opening_bytes for facility_id in opened)
        return Extraction(
            total_bytes=private + facility_bytes,
            facility_bytes=facility_bytes,
            private_bytes=private,
            opened=opened,
            selected=tuple(selected),
            method="evaluate",
            states_evaluated=1,
        )

    def optimistic_lower_bound(self, opened: frozenset[str]) -> int:
        """Admissible size lower bound for beam ordering.

        Unopened facilities are treated as free and every target may choose its cheapest private plan.  The
        bound is intentionally optimistic; it cannot prune away a true byte optimum merely because several
        targets would later share one facility opening cost.
        """
        facility_bytes = sum(self.facilities[facility_id].opening_bytes for facility_id in opened)
        private = sum(min(row.private_bytes for row in rows) for rows in self.by_target.values())
        return facility_bytes + private

    def baseline(self) -> Extraction:
        return _copy_extraction(self.evaluate(frozenset()), method="baseline", states_evaluated=1)

    def components(self) -> tuple[tuple[frozenset[str], frozenset[str]], ...]:
        """Return independent (targets, active facilities) components of the legal sharing graph."""
        facility_targets: dict[str, set[str]] = {facility_id: set() for facility_id in self.active_facilities}
        target_facilities: dict[str, set[str]] = {target: set() for target in self.by_target}
        for target, rows in self.by_target.items():
            for plan in rows:
                target_facilities[target].update(plan.requires)
                for facility_id in plan.requires:
                    facility_targets.setdefault(facility_id, set()).add(target)

        remaining = set(self.by_target)
        components: list[tuple[frozenset[str], frozenset[str]]] = []
        while remaining:
            seed = min(remaining)
            targets = {seed}
            facilities: set[str] = set()
            target_queue = [seed]
            while target_queue:
                target = target_queue.pop()
                for facility_id in sorted(target_facilities[target]):
                    if facility_id in facilities:
                        continue
                    facilities.add(facility_id)
                    for neighbor in sorted(facility_targets.get(facility_id, ())):
                        if neighbor not in targets:
                            targets.add(neighbor)
                            target_queue.append(neighbor)
            remaining.difference_update(targets)
            components.append((frozenset(targets), frozenset(facilities)))
        components.sort(key=lambda row: (min(row[0]), len(row[0]), len(row[1])))
        return tuple(components)


def _copy_extraction(row: Extraction, *, method: str, states_evaluated: int) -> Extraction:
    return Extraction(
        total_bytes=row.total_bytes,
        facility_bytes=row.facility_bytes,
        private_bytes=row.private_bytes,
        opened=row.opened,
        selected=row.selected,
        method=method,
        states_evaluated=states_evaluated,
    )


def exact_extract(problem: Problem, *, max_facilities: int = MAX_EXACT_FACILITIES) -> Extraction:
    """Exhaustive oracle for small active facility sets."""
    facility_ids = tuple(sorted(problem.active_facilities))
    if len(facility_ids) > max_facilities:
        raise ValueError("exact representation extraction exceeds active-facility ceiling")
    best = problem.evaluate(frozenset())
    states = 1
    for width in range(1, len(facility_ids) + 1):
        for combo in combinations(facility_ids, width):
            row = problem.evaluate(frozenset(combo))
            states += 1
            metric = (row.total_bytes, len(row.opened), tuple(sorted(row.opened)), tuple(plan.plan_id for plan in row.selected))
            incumbent = (best.total_bytes, len(best.opened), tuple(sorted(best.opened)), tuple(plan.plan_id for plan in best.selected))
            if metric < incumbent:
                best = row
    return _copy_extraction(best, method="exact", states_evaluated=states)


def beam_extract(
    problem: Problem,
    *,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    max_expansions: int = DEFAULT_MAX_EXPANSIONS,
) -> Extraction:
    """Bounded shared-cost extractor over facility requirement bundles.

    The beam retains states by an admissible optimistic lower bound rather than current total alone.  This lets
    the search temporarily pay a facility opening cost before all of its downstream targets have switched, and
    full requirement bundles allow 2–4-root Mosaic plans to become feasible atomically.
    """
    if type(beam_width) is not int or type(max_rounds) is not int or type(max_expansions) is not int:
        raise ValueError("representation beam budget must use canonical integers")
    if beam_width < 1 or max_rounds < 0 or max_expansions < 1:
        raise ValueError("invalid representation beam budget")

    start = frozenset()
    start_row = problem.evaluate(start)
    best = start_row
    frontier = {start}
    seen = {start}
    states = 1
    expansions = 0

    for _round in range(max_rounds):
        generated: set[frozenset[str]] = set()
        for opened in sorted(frontier, key=lambda row: (len(row), tuple(sorted(row)))):
            for bundle in problem.bundles:
                if bundle <= opened:
                    continue
                candidate = opened | bundle
                if candidate in seen:
                    continue
                generated.add(candidate)
                seen.add(candidate)
                expansions += 1
                if expansions >= max_expansions:
                    break
            if expansions >= max_expansions:
                break
        if not generated:
            break

        ranked = []
        for opened in generated:
            row = problem.evaluate(opened)
            states += 1
            metric = (row.total_bytes, len(row.opened), tuple(sorted(row.opened)), tuple(plan.plan_id for plan in row.selected))
            incumbent = (best.total_bytes, len(best.opened), tuple(sorted(best.opened)), tuple(plan.plan_id for plan in best.selected))
            if metric < incumbent:
                best = row
            ranked.append((
                problem.optimistic_lower_bound(opened),
                row.total_bytes,
                len(opened),
                tuple(sorted(opened)),
                opened,
            ))
        ranked.sort()
        frontier = {row[-1] for row in ranked[:beam_width]}
        if expansions >= max_expansions:
            break

    return _copy_extraction(best, method="beam", states_evaluated=states)


def extract_with_certificate(
    problem: Problem,
    *,
    max_exact_facilities: int = MAX_EXACT_FACILITIES,
    beam_width: int = DEFAULT_BEAM_WIDTH,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    max_expansions: int = DEFAULT_MAX_EXPANSIONS,
) -> tuple[Extraction, dict]:
    """Solve independent sharing components and state whether global optimality was actually proven.

    A production release can require ``optimality_proven=True`` by pruning candidate generators until every
    connected sharing component is small enough for exhaustive extraction.  Research may still inspect a
    bounded beam result for a larger component, but the certificate prevents that heuristic from masquerading
    as the absolute optimum.
    """
    selected: list[Plan] = []
    opened: set[str] = set()
    facility_bytes = private_bytes = states = 0
    component_rows = []
    proven = True
    for targets, facilities in problem.components():
        sub_facilities = [problem.facilities[facility_id] for facility_id in sorted(facilities)]
        sub_plans = [plan for target in sorted(targets) for plan in problem.by_target[target]]
        sub = Problem(sub_facilities, sub_plans, policy=problem.policy)
        if len(sub.active_facilities) <= max_exact_facilities:
            row = exact_extract(sub, max_facilities=max_exact_facilities)
            exact = True
        else:
            row = beam_extract(
                sub,
                beam_width=beam_width,
                max_rounds=max_rounds,
                max_expansions=max_expansions,
            )
            exact = False
            proven = False
        selected.extend(row.selected)
        opened.update(row.opened)
        facility_bytes += row.facility_bytes
        private_bytes += row.private_bytes
        states += row.states_evaluated
        component_rows.append({
            "targets": sorted(targets),
            "facilities": sorted(facilities),
            "active_facilities": len(sub.active_facilities),
            "method": row.method,
            "total_bytes": row.total_bytes,
            "states_evaluated": row.states_evaluated,
            "optimality_proven": exact,
        })

    selected.sort(key=lambda plan: plan.target_id)
    extraction = Extraction(
        total_bytes=facility_bytes + private_bytes,
        facility_bytes=facility_bytes,
        private_bytes=private_bytes,
        opened=frozenset(opened),
        selected=tuple(selected),
        method="component-exact" if proven else "component-hybrid",
        states_evaluated=states,
    )
    if {plan.target_id for plan in extraction.selected} != set(problem.declared_targets):
        raise RuntimeError("component extraction lost a declared target")
    certificate = {
        "optimality_proven": proven,
        "targets": len(problem.declared_targets),
        "active_facilities": len(problem.active_facilities),
        "components": component_rows,
        "max_exact_facilities_per_component": max_exact_facilities,
    }
    return extraction, certificate


def explain(extraction: Extraction) -> dict:
    """Stable JSON-friendly audit surface for benchmark dossiers."""
    return {
        "total_bytes": extraction.total_bytes,
        "facility_bytes": extraction.facility_bytes,
        "private_bytes": extraction.private_bytes,
        "opened": sorted(extraction.opened),
        "selected": [
            {
                "target": plan.target_id,
                "plan": plan.plan_id,
                "kind": plan.representation_kind,
                "private_bytes": plan.private_bytes,
                "requires": sorted(plan.requires),
                "dependency_depth": plan.dependency_depth,
                "read_amplification": plan.read_amplification,
                "peak_memory_bytes": plan.peak_memory_bytes,
                "parser_risk": plan.parser_risk,
            }
            for plan in extraction.selected
        ],
        "method": extraction.method,
        "states_evaluated": extraction.states_evaluated,
    }
