from __future__ import annotations

"""Superseding Shifted nested-stage attribution with causally supported mtime normalization.

V1 is immutable and invalid. This instrument changes only fixture metadata before either inherited child
runs; it reuses V1's exact child/stage instrumentation and unchanged 0.80/0.20 decision bands.
"""

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import statistics

from benchmarks import v030_release_performance as PERF
from benchmarks import v030_shifted_g04_nested_stage_attribution as V1

TARGET = V1.TARGET
REPETITIONS = V1.REPETITIONS
STAGE_DOMINANT_RATIO = V1.STAGE_DOMINANT_RATIO
MATERIAL_SECONDARY_RATIO = V1.MATERIAL_SECONDARY_RATIO
FIXED_NS = 1_767_225_600_000_000_000
EXPECTED_TREE = "d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd"


def _fix_times(root: Path) -> None:
    paths = [root, *sorted(root.rglob("*"), key=lambda p: os.fsencode(p.relative_to(root)))]
    for path in paths:
        os.utime(path, ns=(FIXED_NS, FIXED_NS), follow_symlinks=False)


def _all_mtimes_fixed(root: Path) -> bool:
    paths = [root, *root.rglob("*")]
    return all(path.stat(follow_symlinks=False).st_mtime_ns == FIXED_NS for path in paths)


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    before_tree = PERF.GENERAL._historical_treehash(source)
    _fix_times(source)
    after_tree = PERF.GENERAL._historical_treehash(source)
    mtimes_fixed = _all_mtimes_fixed(source)

    rows = []
    for rep in range(1, REPETITIONS + 1):
        order = ("v028", "attempt5") if rep % 2 else ("attempt5", "v028")
        measured = {}
        for kind in order:
            measured[kind] = V1._fresh(kind, source, work_root / f"rep-{rep}-{kind}.cmpct")
        rows.append({"rep": rep, "order": list(order), **measured})

    invalid: list[str] = []
    if before_tree != EXPECTED_TREE:
        invalid.append("source_tree_before")
    if after_tree != EXPECTED_TREE:
        invalid.append("source_tree_after")
    if not mtimes_fixed:
        invalid.append("mtime_normalization")

    identities = {}
    for kind in ("v028", "attempt5"):
        sizes = {int(row[kind]["archive_bytes"]) for row in rows}
        shas = {row[kind]["archive_sha256"] for row in rows}
        identities[kind] = {"archive_bytes": sorted(sizes), "archive_sha256": sorted(shas)}
        if len(sizes) != 1:
            invalid.append(f"{kind}:archive_bytes_nondeterministic")
        if len(shas) != 1:
            invalid.append(f"{kind}:archive_sha_nondeterministic")

    for row in rows:
        for kind in ("v028", "attempt5"):
            item = row[kind]
            checks = {
                "positive_child": math.isfinite(float(item["child_s"])) and float(item["child_s"]) > 0,
                "verify": item["verify_ok"] is True,
                "tree_identity": item["tree_sha256"] == EXPECTED_TREE,
                "single_stage_calls": (
                    int(item["legacy_calls"]) == 1 and int(item["graph_calls"]) == 1
                    if kind == "v028"
                    else int(item["placement_calls"]) == 1 and int(item["residual_calls"]) == 1
                ),
            }
            stage_fields = ("legacy_s", "graph_s") if kind == "v028" else ("placement_s", "residual_s")
            checks["finite_stages"] = all(math.isfinite(float(item[k])) and float(item[k]) >= 0 for k in stage_fields)
            item["checks"] = checks
            invalid.extend(f"rep-{row['rep']}:{kind}:{name}" for name, ok in checks.items() if not ok)

    def med(kind: str, field: str) -> float:
        return float(statistics.median(float(row[kind][field]) for row in rows))

    vc, vl, vg = med("v028", "child_s"), med("v028", "legacy_s"), med("v028", "graph_s")
    ac, ap, ar = med("attempt5", "child_s"), med("attempt5", "placement_s"), med("attempt5", "residual_s")
    ratios = {
        "v028_legacy_ratio": vl / max(vc, 1e-12),
        "v028_graph_ratio": vg / max(vc, 1e-12),
        "attempt5_placement_ratio": ap / max(ac, 1e-12),
        "attempt5_residual_ratio": ar / max(ac, 1e-12),
    }
    if invalid:
        decision = "INVALID"
    elif ratios["v028_graph_ratio"] >= STAGE_DOMINANT_RATIO and ratios["attempt5_placement_ratio"] >= STAGE_DOMINANT_RATIO:
        decision = "SHIFTED_G04_SHARED_NESTED_GRAPH_CONSTRUCTION_OWNS"
    elif ratios["v028_legacy_ratio"] >= MATERIAL_SECONDARY_RATIO and ratios["attempt5_residual_ratio"] < MATERIAL_SECONDARY_RATIO:
        decision = "SHIFTED_G04_SHARED_V028_LEGACY_STAGE_MATERIAL"
    elif ratios["attempt5_residual_ratio"] >= MATERIAL_SECONDARY_RATIO and ratios["v028_legacy_ratio"] < MATERIAL_SECONDARY_RATIO:
        decision = "SHIFTED_G04_SHARED_ATTEMPT5_RESIDUAL_STAGE_MATERIAL"
    else:
        decision = "SHIFTED_G04_SHARED_NESTED_STAGE_MIXED"

    return {
        "schema": "cmpct-v030-shifted-g04-nested-stage-attribution-v2",
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "target": "/".join(TARGET),
        "fixture": {"fixed_ns": FIXED_NS, "tree_before": before_tree, "tree_after": after_tree, "mtimes_fixed": mtimes_fixed},
        "identities": identities,
        "rows": rows,
        "medians": {"v028_child_s": vc, "v028_legacy_s": vl, "v028_graph_s": vg, "attempt5_child_s": ac, "attempt5_placement_s": ap, "attempt5_residual_s": ar, **ratios},
        "decision": decision,
        "invalid_reasons": invalid,
        "contract": {"repetitions": REPETITIONS, "stage_dominant_ratio": STAGE_DOMINANT_RATIO, "material_secondary_ratio": MATERIAL_SECONDARY_RATIO, "expected_tree": EXPECTED_TREE, "fixed_ns": FIXED_NS, "instrumentation_only": True, "product_changed": False, "release_credit": False},
        "release_credit": False,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"], "medians": result["medians"], "identities": result["identities"]}, separators=(",", ":")))


if __name__ == "__main__":
    main()
