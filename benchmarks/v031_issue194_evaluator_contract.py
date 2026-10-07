from __future__ import annotations

"""Pure Issue #194 promotion evaluator law.

No benchmark mechanism lives here. The contract compiles four paired reps,
exact semantics, direct ownership proof, held-out slowdown/RSS gates,
complete-product gates, and causal terminal routing.
"""

from dataclasses import dataclass
from statistics import median
from typing import Iterable

REL_SLOWDOWN = 0.05
ABS_SLOWDOWN_S = 0.003
SHIFTED_WALL_MAX = 0.90
SHIFTED_CPU_MAX = 1.0
CHILD_RSS_MAX = 1.10
PRODUCT_RSS_MAX = 1.25

WORKLOADS = (
    "01_shifted_versions",
    "03_boundary_churn",
    "02_false_neighbors",
    "05_incompressible",
)
HELD_OUT = WORKLOADS[1:]
CHILD_KINDS = ("v028", "attempt5")


@dataclass(frozen=True)
class Pair:
    baseline_wall_s: float
    candidate_wall_s: float
    baseline_cpu_s: float
    candidate_cpu_s: float
    rss_ratio: float


def confirmed_slowdown(baseline_s: float, candidate_s: float) -> bool:
    return (
        candidate_s - baseline_s > ABS_SLOWDOWN_S
        and candidate_s > baseline_s * (1.0 + REL_SLOWDOWN)
    )


def summarize_pairs(pairs: Iterable[Pair]) -> dict:
    rows = list(pairs)
    if len(rows) != 4:
        raise ValueError("Issue194 hardened court requires exactly four paired repetitions")
    b_wall = median(row.baseline_wall_s for row in rows)
    c_wall = median(row.candidate_wall_s for row in rows)
    return {
        "baseline_wall_median_s": b_wall,
        "candidate_wall_median_s": c_wall,
        "wall_ratio_median": median(
            row.candidate_wall_s / max(1e-12, row.baseline_wall_s) for row in rows
        ),
        "cpu_ratio_median": median(
            row.candidate_cpu_s / max(1e-12, row.baseline_cpu_s) for row in rows
        ),
        "rss_ratio_max": max(row.rss_ratio for row in rows),
        "confirmed_wall_slowdown": confirmed_slowdown(b_wall, c_wall),
    }


def evaluate_child(rows: dict, semantic: dict) -> dict:
    missing = [
        f"{name}/{kind}"
        for name in WORKLOADS
        for kind in CHILD_KINDS
        if name not in rows
        or kind not in rows[name]
        or name not in semantic
        or kind not in semantic[name]
    ]
    if missing:
        raise ValueError(f"missing frozen child rows: {missing}")

    shifted = []
    for kind in CHILD_KINDS:
        row = rows["01_shifted_versions"][kind]
        shifted.append({
            "kind": kind,
            "positive": (
                row["wall_ratio_median"] <= SHIFTED_WALL_MAX
                and row["cpu_ratio_median"] < SHIFTED_CPU_MAX
            ),
            "wall_ratio_median": row["wall_ratio_median"],
            "cpu_ratio_median": row["cpu_ratio_median"],
        })

    held_out_failures = [
        {"name": name, "kind": kind}
        for name in HELD_OUT for kind in CHILD_KINDS
        if rows[name][kind]["confirmed_wall_slowdown"]
    ]
    exact_failures = [
        {"name": name, "kind": kind}
        for name in WORKLOADS for kind in CHILD_KINDS
        if (
            not rows[name][kind].get("archive_identity_exact", False)
            or not rows[name][kind].get("tree_identity_exact", False)
        )
    ]
    rss_failures = [
        {"name": name, "kind": kind, "rss_ratio_max": rows[name][kind]["rss_ratio_max"]}
        for name in WORKLOADS for kind in CHILD_KINDS
        if rows[name][kind]["rss_ratio_max"] > CHILD_RSS_MAX
    ]

    semantic_failures = []
    ownership_failures = []
    for name in WORKLOADS:
        for kind in CHILD_KINDS:
            proof = semantic[name][kind]
            exact = proof.get("exact", False)
            exact_ok = all(exact.values()) if isinstance(exact, dict) else bool(exact)
            if not exact_ok:
                semantic_failures.append({"name": name, "kind": kind})
            expected = proof.get("expected_base_index_builds")
            observed = proof.get("semantic_candidate_dict_build_count")
            timed = list(proof.get("timed_candidate_dict_build_counts", []))
            if expected is None or observed != expected:
                ownership_failures.append({
                    "name": name, "kind": kind, "reason": "semantic_ownership",
                    "expected": expected, "observed": observed,
                })
            if len(timed) != 4:
                ownership_failures.append({
                    "name": name, "kind": kind, "reason": "timed_ownership_count",
                    "expected_repetitions": 4, "observed_repetitions": len(timed),
                })
            else:
                for rep, value in enumerate(timed):
                    if value != expected:
                        ownership_failures.append({
                            "name": name, "kind": kind, "reason": "timed_ownership",
                            "rep": rep, "expected": expected, "observed": value,
                        })

    passed = (
        any(item["positive"] for item in shifted)
        and not held_out_failures
        and not exact_failures
        and not rss_failures
        and not semantic_failures
        and not ownership_failures
    )
    return {
        "passed": passed,
        "shifted_positive_rows": shifted,
        "held_out_failures": held_out_failures,
        "exact_failures": exact_failures,
        "rss_failures": rss_failures,
        "semantic_failures": semantic_failures,
        "ownership_failures": ownership_failures,
    }


def evaluate_product(rows: dict) -> dict:
    """Evaluate timed complete-product evidence after custody already succeeded.

    Source/process custody is an execution precondition in the hardened runner:
    custody mismatch raises before any timed product evidence is accepted. It is
    therefore not a product-efficiency failure and must not be routed through
    NARROW_TO_EFFICIENCY_DEBT.
    """
    failures = []
    for name in WORKLOADS:
        row = rows.get(name)
        if row is None:
            failures.append({"name": name, "reason": "missing"})
            continue
        if not row.get("archive_identity_exact", False) or not row.get("tree_identity_exact", False):
            failures.append({"name": name, "reason": "identity"})
        if row.get("confirmed_wall_slowdown", True):
            failures.append({"name": name, "reason": "confirmed_wall_slowdown"})
        if row.get("rss_ratio_max", float("inf")) > PRODUCT_RSS_MAX:
            failures.append({"name": name, "reason": "rss"})
        if row.get("rss_samples_min", 0) <= 0:
            failures.append({"name": name, "reason": "zero_rss_samples"})
    return {"passed": not failures, "failures": failures}


def decision(child: dict, product: dict | None) -> str:
    if not child["passed"]:
        return "RETIRE_OR_NARROW_GROUPED_DICT_OWNERSHIP"
    if product is None:
        return "ADVANCE_TO_PRODUCT_AB"
    return "ADVANCE_GROUPED_DICT_OWNERSHIP" if product["passed"] else "NARROW_TO_EFFICIENCY_DEBT"
