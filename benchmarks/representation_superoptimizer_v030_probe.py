from __future__ import annotations

"""Mechanism-level falsifier for the v0.30 shared-cost Representation Superoptimizer extractor.

This is not a compression-ratio benchmark.  It uses pre-priced synthetic representation candidates to prove
three optimizer properties before the machinery is allowed near real archive candidates:

1. shared opening cost can reverse a locally-greedy representation choice;
2. multi-root requirement bundles must be considered atomically;
3. the bounded beam must reproduce an exhaustive oracle on these preregistered counterexamples.

A green result establishes only extraction semantics.  Real stored-byte improvement still has to be earned by
feeding complete Mosaic/Geometry/Substrate candidate costs from exact public archives in a later integration.
"""

import argparse
import json
from pathlib import Path

from experiments import representation_superoptimizer_v030_safe as RSO


def _fallback(target: str, cost: int) -> RSO.Plan:
    return RSO.Plan(target, f"direct-{target}", cost, representation_kind="direct")


def _local_charge(problem: RSO.Problem) -> int:
    """Deliberately phase-ordered/local comparator that charges every target its facilities independently."""
    total = 0
    for rows in problem.by_target.values():
        best = None
        for plan in rows:
            cost = plan.private_bytes + sum(problem.facilities[facility].opening_bytes for facility in plan.requires)
            metric = (cost, plan.plan_id)
            if best is None or metric < best:
                best = metric
        if best is None:
            raise RuntimeError("local comparator lost target")
        total += best[0]
    return total


def _case_shared_root() -> tuple[str, RSO.Problem]:
    facilities = [RSO.Facility("root", 120, "mosaic-root")]
    plans = [
        _fallback("a", 100), _fallback("b", 100),
        RSO.Plan("a", "ref-a", 10, frozenset({"root"}), dependency_depth=1, representation_kind="reference"),
        RSO.Plan("b", "ref-b", 10, frozenset({"root"}), dependency_depth=1, representation_kind="reference"),
    ]
    return "shared_root_amortization", RSO.Problem(facilities, plans)


def _case_geometry_reference_flip() -> tuple[str, RSO.Problem]:
    facilities = [RSO.Facility("version-root", 80, "prefix-root")]
    plans = [
        _fallback("v1", 100), _fallback("v2", 100),
        RSO.Plan("v1", "geometry-v1", 60, representation_kind="geometry"),
        RSO.Plan("v2", "geometry-v2", 60, representation_kind="geometry"),
        RSO.Plan("v1", "prefix-v1", 10, frozenset({"version-root"}), dependency_depth=1, representation_kind="prefix"),
        RSO.Plan("v2", "prefix-v2", 10, frozenset({"version-root"}), dependency_depth=1, representation_kind="prefix"),
    ]
    return "geometry_vs_shared_reference", RSO.Problem(facilities, plans)


def _case_multiroot_atom() -> tuple[str, RSO.Problem]:
    facilities = [
        RSO.Facility("root-a", 28, "mosaic-root"),
        RSO.Facility("root-b", 31, "mosaic-root"),
        RSO.Facility("atom", 45, "synthetic-atom"),
    ]
    plans = [
        _fallback("x", 115), _fallback("y", 95), _fallback("z", 80),
        RSO.Plan("x", "mosaic-x", 8, frozenset({"root-a", "root-b"}), dependency_depth=1,
                 read_amplification=3.5, representation_kind="mosaic"),
        RSO.Plan("y", "atom-y", 12, frozenset({"atom"}), dependency_depth=1,
                 read_amplification=2.0, representation_kind="substrate"),
        RSO.Plan("z", "atom-z", 14, frozenset({"atom"}), dependency_depth=1,
                 read_amplification=2.0, representation_kind="substrate"),
    ]
    return "multiroot_plus_synthetic_atom", RSO.Problem(facilities, plans)


def run() -> dict:
    rows = []
    for name, problem in (_case_shared_root(), _case_geometry_reference_flip(), _case_multiroot_atom()):
        baseline = problem.baseline()
        local = _local_charge(problem)
        exact = RSO.exact_extract(problem)
        beam = RSO.beam_extract(problem, beam_width=32, max_rounds=8, max_expansions=1000)
        rows.append({
            "name": name,
            "baseline_bytes": baseline.total_bytes,
            "phase_ordered_local_bytes": local,
            "exact_global_bytes": exact.total_bytes,
            "beam_global_bytes": beam.total_bytes,
            "saving_vs_baseline_bytes": baseline.total_bytes - exact.total_bytes,
            "saving_vs_phase_ordered_local_bytes": local - exact.total_bytes,
            "exact": RSO.explain(exact),
            "beam": RSO.explain(beam),
            "beam_matches_exact": beam.total_bytes == exact.total_bytes,
        })
    totals = {
        "cases": len(rows),
        "all_beam_match_exact": all(row["beam_matches_exact"] for row in rows),
        "aggregate_baseline_bytes": sum(row["baseline_bytes"] for row in rows),
        "aggregate_phase_ordered_local_bytes": sum(row["phase_ordered_local_bytes"] for row in rows),
        "aggregate_global_bytes": sum(row["exact_global_bytes"] for row in rows),
        "global_saving_vs_baseline_bytes": sum(row["saving_vs_baseline_bytes"] for row in rows),
        "global_saving_vs_phase_ordered_local_bytes": sum(row["saving_vs_phase_ordered_local_bytes"] for row in rows),
        "max_beam_states": max(row["beam"]["states_evaluated"] for row in rows),
        "mechanism_gate": (
            all(row["beam_matches_exact"] for row in rows)
            and all(row["exact_global_bytes"] <= row["phase_ordered_local_bytes"] for row in rows)
            and any(row["exact_global_bytes"] < row["phase_ordered_local_bytes"] for row in rows)
        ),
    }
    return {
        "schema": "cmpct-v030-rso-phase-ordering-probe-v1",
        "status": "CHILD_RESEARCH_OPTIMIZER_SEMANTICS_NOT_ARCHIVE_BENCHMARK",
        "claim_boundary": (
            "Pre-priced synthetic representation plans only. Demonstrates shared-cost extraction/phase-ordering "
            "semantics; makes no claim about CMPCT archive size until real complete candidate costs are wired in."
        ),
        "contract": {
            "expected_cases": 3,
            "beam_width": 32,
            "max_rounds": 8,
            "max_expansions": 1000,
            "require_all_beam_match_exact": True,
            "require_strict_phase_ordering_counterexample": True,
        },
        "rows": rows,
        "totals": totals,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["totals"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
