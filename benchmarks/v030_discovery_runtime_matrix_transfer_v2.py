from __future__ import annotations

"""Superseding transfer A/B for the position-independent discovery source.

Scientifically identical to v1. V2 changes only receipt robustness: supporting ratios with a non-positive or
non-finite denominator serialize as null so the inherited validity grammar can return INVALID instead of the
instrument crashing. Research evidence only; no product or release credit.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_release_performance as PERF
from benchmarks import v030_shifted_g04_discovery_audition_survival_v1 as SURV

TARGETS = PERF.TARGETS
REPETITIONS = 2


def _median(rows: list[dict], kind: str, field: str) -> float:
    return float(statistics.median(float(row[kind][field]) for row in rows))


def _ratio_or_none(numerator: float, denominator: float) -> float | None:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator <= 0:
        return None
    return numerator / denominator


def _self_check_ratio_serialization() -> None:
    """Lock the exact infrastructure repair that supersedes the crashed v1 receipt."""
    assert _ratio_or_none(1.0, 0.0) is None
    assert _ratio_or_none(1.0, -1.0) is None
    assert _ratio_or_none(1.0, float("nan")) is None
    assert _ratio_or_none(float("inf"), 1.0) is None
    assert _ratio_or_none(2.0, 4.0) == 0.5


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    results = []
    invalid: list[str] = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        rows = []
        for rep in range(1, REPETITIONS + 1):
            order = ("baseline", "inherited-only") if rep % 2 else ("inherited-only", "baseline")
            measured = {}
            for kind in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{rep}-{kind}.cmpct"
                archive.parent.mkdir(parents=True, exist_ok=True)
                measured[kind] = SURV._fresh(kind, source, archive)
            rows.append({"rep": rep, "order": list(order), **measured})

        expected_tree = rows[0]["baseline"]["tree_sha256"]
        for row in rows:
            for kind in ("baseline", "inherited-only"):
                item = row[kind]
                checks = {
                    "verify": item["verify_ok"] is True,
                    "tree_identity": item["tree_sha256"] == expected_tree,
                    "positive_child": math.isfinite(float(item["child_s"])) and float(item["child_s"]) > 0,
                    "positive_delta": math.isfinite(float(item["delta_s"])) and float(item["delta_s"]) > 0,
                    "positive_calls": int(item["delta_calls"]) > 0,
                }
                item["checks"] = checks
                invalid.extend(
                    f"{suite}/{name}:rep-{row['rep']}:{kind}:{key}"
                    for key, ok in checks.items() if not ok
                )

        deterministic = {}
        for kind in ("baseline", "inherited-only"):
            sizes = {int(row[kind]["archive_bytes"]) for row in rows}
            shas = {row[kind]["archive_sha256"] for row in rows}
            deterministic[kind] = len(sizes) == 1 and len(shas) == 1
            if not deterministic[kind]:
                invalid.append(f"{suite}/{name}:{kind}:archive-nondeterministic")

        baseline_bytes = int(rows[0]["baseline"]["archive_bytes"])
        inherited_bytes = int(rows[0]["inherited-only"]["archive_bytes"])
        baseline_sha = rows[0]["baseline"]["archive_sha256"]
        inherited_sha = rows[0]["inherited-only"]["archive_sha256"]
        baseline_calls = _median(rows, "baseline", "delta_calls")
        inherited_calls = _median(rows, "inherited-only", "delta_calls")
        baseline_child = _median(rows, "baseline", "child_s")
        inherited_child = _median(rows, "inherited-only", "child_s")
        baseline_delta = _median(rows, "baseline", "delta_s")
        inherited_delta = _median(rows, "inherited-only", "delta_s")

        results.append({
            "suite": suite,
            "name": name,
            "tree_sha256": expected_tree,
            "rows": rows,
            "baseline_bytes": baseline_bytes,
            "inherited_only_bytes": inherited_bytes,
            "byte_delta": inherited_bytes - baseline_bytes,
            "baseline_sha256": baseline_sha,
            "inherited_only_sha256": inherited_sha,
            "byte_identical": baseline_bytes == inherited_bytes and baseline_sha == inherited_sha,
            "baseline_delta_calls_median": baseline_calls,
            "inherited_only_delta_calls_median": inherited_calls,
            "delta_call_reduction_fraction": (baseline_calls - inherited_calls) / max(1.0, baseline_calls),
            "baseline_child_median_s": baseline_child,
            "inherited_only_child_median_s": inherited_child,
            "child_wall_ratio": _ratio_or_none(inherited_child, baseline_child),
            "baseline_delta_median_s": baseline_delta,
            "inherited_only_delta_median_s": inherited_delta,
            "delta_wall_ratio": _ratio_or_none(inherited_delta, baseline_delta),
        })

    if invalid:
        decision = "INVALID"
    else:
        all_identical = all(row["byte_identical"] for row in results)
        at_least_one_call_reduction = any(row["delta_call_reduction_fraction"] > 0 for row in results)
        any_larger = any(row["byte_delta"] > 0 for row in results)
        any_smaller = any(row["byte_delta"] < 0 for row in results)
        if all_identical and at_least_one_call_reduction:
            decision = "DISCOVERY_SOURCE_RUNTIME_MATRIX_BYTE_DEAD"
        elif any_smaller and not any_larger:
            decision = "DISCOVERY_SOURCE_RUNTIME_MATRIX_ALTERNATE_SMALLER"
        else:
            decision = "DISCOVERY_SOURCE_TRANSFER_MIXED"

    return {
        "schema": "cmpct-v030-discovery-runtime-matrix-transfer-v2",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "decision": decision,
        "invalid_reasons": invalid,
        "targets": results,
        "contract": {
            "targets": [list(target) for target in TARGETS],
            "repetitions": REPETITIONS,
            "single_ablation": "accepted.BASE.P._position_independent_candidates -> []",
            "product_changed": False,
            "release_credit": False,
            "supersedes": "cmpct-v030-discovery-runtime-matrix-transfer-v1",
            "mechanical_change": "non-positive/non-finite ratio denominator serializes as null; validity grammar unchanged",
        },
        "release_credit": False,
    }


def main() -> None:
    _self_check_ratio_serialization()
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "decision": result["decision"],
        "invalid_reasons": result["invalid_reasons"],
        "targets": [
            {
                "target": f"{row['suite']}/{row['name']}",
                "byte_delta": row["byte_delta"],
                "delta_call_reduction_fraction": row["delta_call_reduction_fraction"],
                "child_wall_ratio": row["child_wall_ratio"],
                "delta_wall_ratio": row["delta_wall_ratio"],
            }
            for row in result["targets"]
        ],
    }, separators=(",", ":")))


if __name__ == "__main__":
    main()
