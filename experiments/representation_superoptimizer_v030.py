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

Footnote: all numbers accepted by this core are already-computed *complete local costs*.  It never estimates
compression ratio from entropy or file type.  Representation generators remain responsible for exact inverse
proofs and descriptor/framing charges before a Plan reaches this extractor.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

MAX_REQUIREMENTS_PER_PLAN = 4
DEFAULT_BEAM_WIDTH = 64
DEFAULT_MAX_ROUNDS = 16
DEFAULT_MAX_EXPANSIONS = 20_000
MAX_EXACT_FACILITIES = 18


@dataclass(frozen=True, slots=True)
class Policy:
    """Hard representation boundary applied before any size optimization."""

    max_dependency_depth: int = 1
    max_read_amplification: float = 8.0
    max_peak_memory_bytes: int = 512 * 1024 * 1024
    max_parser_risk: int = 3


@dataclass(frozen=True, slots=True)
class Facility:
    facility_id: str
    opening_bytes: int
    kind: str = "shared-basis"

    def __post_init__(self) -> None:
        if not self.facility_id or self.opening_bytes < 0:
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
        if not self.target_id or not self.plan_id or self.private_bytes < 0:
            raise ValueError("invalid representation plan")
        if len(self.requires) > MAX_REQUIREMENTS_PER_PLAN:
            raise ValueError("representation plan exceeds shared-requirement ceiling")
        if self.dependency_depth < 0 or self.read_amplification < 0 or self.peak_memory_bytes < 0:
            raise ValueError("negative representation resource declaration")
        if self.parser_risk < 0:
            raise ValueError("negative parser-risk declaration")


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
        if not by_target:
            raise ValueError("representation problem has no legal targets")
        for target, rows in by_target.items():
            if not any(not row.requires for row in rows):
                # Footnote: every logical target needs a self-contained fallback.  This is the optimizer-level
                # analogue of CMPCT's exact workload fallback: shared facilities may improve a target, but the
                # solver is never allowed to make reconstruction contingent on opening them.
                raise ValueError(f"target {target} lacks a facility-free fallback")
            rows.sort(key=self._plan_rank)
        self.by_target = dict(sorted(by_target.items()))

        bundles = {plan.requires for rows in self.by_target.values() for plan in rows if plan.requires}
        # Opening a candidate's full requirement bundle in one transition is essential for Mosaic-like plans:
        # neither of two roots may be useful alone even though the pair is globally profitable.
        self.bundles = tuple(sorted(bundles, key=lambda bundle: (len(bundle), tuple(sorted(bundle)))))

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
        if not opened <= self.facilities.keys():
            raise ValueError("unknown opened facility")
        selected: list[Plan] = []
        private = 0
        for rows in self.by_target.values():
            feasible = [plan for plan in rows if plan.requires <= opened]
            if not feasible:
                raise RuntimeError("representation target lost its facility-free fallback")
            winner = min(feasible, key=self._plan_rank)
            selected.append(winner)
            private += winner.private_bytes
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
        row = self.evaluate(frozenset())
        return Extraction(**{**row.__dict__, "method": "baseline"})  # type: ignore[attr-defined]


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
    """Exhaustive research oracle for small candidate sets.

    This is a falsifier/reference implementation, not the production search strategy.  It makes small tests
    capable of proving whether the bounded beam lost a shared-cost optimum.
    """
    facility_ids = tuple(sorted(problem.facilities))
    if len(facility_ids) > max_facilities:
        raise ValueError("exact representation extraction exceeds facility ceiling")
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
        for opened in frontier:
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
