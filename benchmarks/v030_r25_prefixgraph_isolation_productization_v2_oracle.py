from __future__ import annotations

"""Superseding frozen S6 Hostile Reviewer with causally stabilized Shifted mtimes.

The productization mechanism and decision bands are inherited unchanged from v1.  The sole scientific
change is the preregistered fixture intervention proven by R25_SHIFTED_SERIALIZED_METADATA_CAUSAL_V2_RESULT.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess

from benchmarks import v030_r25_prefixgraph_isolation_productization_oracle as V1
from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_V2_PREREG.md"
ORDER = (("control", "candidate"), ("candidate", "control"))
FIXED_MTIME_NS = 1_767_225_600_000_000_000
R24_BYTES = 29_883_488
R24_SHA256 = "a3192a1462e37282e5128e50c3b20a039ca26821d5ceb2508958d6e3918bbc22"


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _normalize_mtime(root: Path) -> None:
    paths = sorted([root, *root.rglob("*")], key=lambda p: len(p.relative_to(root).parts), reverse=True)
    for path in paths:
        os.utime(path, ns=(FIXED_MTIME_NS, FIXED_MTIME_NS), follow_symlinks=False)
    for path in [root, *root.rglob("*")]:
        actual = int(path.lstat().st_mtime_ns)
        if actual != FIXED_MTIME_NS:
            raise RuntimeError(f"frozen mtime normalization failed: {path}: {actual}")


def _r24_identity(source: Path, destination: Path) -> tuple[int, str]:
    destination.unlink(missing_ok=True)
    PRODUCT._locality_bounded_r24_build(source, destination)
    return destination.stat().st_size, _sha(destination)


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    historical_tree_before = str(GENERAL._historical_treehash(source))
    if historical_tree_before != expected_historical_tree:
        raise RuntimeError("S6 v2 source drifted from accepted repaired Shifted authority")

    _normalize_mtime(source)
    historical_tree_after = str(GENERAL._historical_treehash(source))
    product_tree = str(CANONICAL.treehash(source))
    if historical_tree_after != expected_historical_tree:
        raise RuntimeError("mtime normalization changed accepted Shifted content identity")

    preflight_r24 = work_root / "custody" / "preflight-r24.cmpct"
    preflight_r24.parent.mkdir(parents=True, exist_ok=True)
    preflight_bytes, preflight_sha = _r24_identity(source, preflight_r24)
    if (preflight_bytes, preflight_sha) != (R24_BYTES, R24_SHA256):
        raise RuntimeError(
            f"normalized genuine-r24 identity mismatch: {(preflight_bytes, preflight_sha)} != {(R24_BYTES, R24_SHA256)}"
        )

    rows: list[dict] = []
    failures: list[dict] = []
    counts = {"control": 0, "candidate": 0}
    for round_index, modes in enumerate(ORDER):
        for position, mode in enumerate(modes):
            counts[mode] += 1
            archive = work_root / "archives" / f"round{round_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            row = V1._run(mode, source, archive)
            row["round_index"] = round_index
            row["position"] = position

            probe = work_root / "custody" / f"round{round_index}-{position}-{mode}-r24.cmpct"
            probe_bytes, probe_sha = _r24_identity(source, probe)
            row["r24_custody_bytes"] = probe_bytes
            row["r24_custody_sha256"] = probe_sha
            rows.append(row)

            receipt = row.get("prefixgraph_process_receipt") or {}
            common_ok = (
                not row.get("worker_failed")
                and row.get("mode") == mode
                and row.get("expected_tree_sha256") == product_tree
                and row.get("tree_sha256") == product_tree
                and row.get("r25_selected") == "prefixgraph"
                and int(row.get("r24_product_bytes", -1)) == R24_BYTES
                and probe_bytes == R24_BYTES
                and probe_sha == R24_SHA256
                and row.get("selected") == "prefixgraph"
                and int(row.get("format_revision", -1)) == 25
                and int(row.get("tree_peak_rss_kib", 0)) > 0
                and int(row.get("tree_samples", 0)) >= 100
                and row.get("tree_sampler_errors") == []
                and float(row.get("tree_sampler_interval_s", 1.0)) <= 0.01
                and row.get("canonical_r25_build_restored") is True
                and row.get("executor_restored") is True
            )
            if mode == "candidate":
                common_ok = common_ok and (
                    row.get("r25_candidate_scheduler") == "prefixgraph-process-level15-then-g04-main-v1"
                    and row.get("audited_executor_constructions") == 1
                    and row.get("audited_executor_submissions") == 1
                    and row.get("audited_child_dead_on_submit_return") == [True]
                    and receipt.get("schema") == "cmpct-v030-prefixgraph-process-executor-v1"
                    and receipt.get("semantic_owner") == "experiments._v030_canonical_prefixgraph"
                    and int(receipt.get("prefix_level", -1)) == 15
                    and int(receipt.get("archive_bytes", -1)) > 0
                    and isinstance(receipt.get("archive_sha256"), str)
                    and len(receipt.get("archive_sha256", "")) == 64
                )
            else:
                common_ok = common_ok and (
                    row.get("r25_candidate_scheduler") == "g04-main-plus-one-prefixgraph-worker-v2"
                    and row.get("prefixgraph_process_receipt") is None
                )
            if not common_ok:
                failures.append({"round": round_index, "position": position, **row})

    hostile_rows = []
    for index, mode in enumerate(("missing-helper", "malformed-receipt")):
        archive = work_root / "hostile" / f"{index}-{mode}.cmpct"
        archive.parent.mkdir(parents=True, exist_ok=True)
        row = V1._run(mode, source, archive)
        hostile_rows.append(row)
        if row.get("worker_failed") or row.get("mode") != mode or row.get("failed_closed") is not True:
            failures.append({"hostile": mode, **row})

    summaries: dict[str, dict] = {}
    deterministic: dict[str, bool] = {}
    for mode in ("control", "candidate"):
        mode_rows = [row for row in rows if row.get("mode") == mode and not row.get("worker_failed")]
        identities = {
            tuple(row.get(key) for key in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected", "format_revision",
                "r24_product_bytes", "r25_product_bytes", "r25_selected", "r24_custody_bytes", "r24_custody_sha256",
            ))
            for row in mode_rows
        }
        deterministic[mode] = len(mode_rows) == 2 and len(identities) == 1
        if len(mode_rows) == 2:
            summaries[mode] = {
                "archive_bytes": int(mode_rows[0]["archive_bytes"]),
                "archive_sha256": mode_rows[0]["archive_sha256"],
                "r24_product_bytes": int(mode_rows[0]["r24_product_bytes"]),
                "r24_custody_sha256": mode_rows[0]["r24_custody_sha256"],
                "r25_product_bytes": int(mode_rows[0]["r25_product_bytes"]),
                "median_tree_peak_rss_kib": _median(mode_rows, "tree_peak_rss_kib"),
                "median_parent_peak_ru_maxrss_kib": _median(mode_rows, "parent_peak_ru_maxrss_kib"),
                "median_wall_s": _median(mode_rows, "wall_s"),
                "median_tree_samples": _median(mode_rows, "tree_samples"),
                "deterministic": deterministic[mode],
            }

    valid = (
        not failures
        and counts == {"control": 2, "candidate": 2}
        and set(summaries) == {"control", "candidate"}
        and all(deterministic.values())
        and all(row.get("failed_closed") is True for row in hostile_rows)
        and preflight_bytes == R24_BYTES
        and preflight_sha == R24_SHA256
    )

    derived: dict[str, float | int | bool] = {}
    decision = "INVALID_PRODUCTIZATION_RECEIPT"
    if valid:
        control = summaries["control"]
        candidate = summaries["candidate"]
        control_peak = float(control["median_tree_peak_rss_kib"])
        candidate_peak = float(candidate["median_tree_peak_rss_kib"])
        control_wall = float(control["median_wall_s"])
        candidate_wall = float(candidate["median_wall_s"])
        size_penalty = int(candidate["archive_bytes"]) - int(control["archive_bytes"])
        size_ratio = size_penalty / max(1, int(control["archive_bytes"]))
        rss_reduction = 1.0 - candidate_peak / control_peak
        wall_ratio = candidate_wall / control_wall
        byte_budget_ok = size_penalty <= 8192 and size_ratio <= 0.005
        derived = {
            "candidate_tree_peak_reduction_fraction_vs_control": rss_reduction,
            "candidate_wall_ratio_vs_control": wall_ratio,
            "candidate_archive_size_penalty_bytes_vs_control": size_penalty,
            "candidate_archive_size_penalty_ratio_vs_control": size_ratio,
            "byte_budget_ok": byte_budget_ok,
            "hostile_fail_closed": all(row.get("failed_closed") is True for row in hostile_rows),
        }
        if rss_reduction < 0.20:
            decision = "PREFIXGRAPH_ISOLATION_PRODUCTIZATION_DID_NOT_TRANSFER"
        elif wall_ratio > 1.10 or not byte_budget_ok:
            decision = "PREFIXGRAPH_ISOLATION_EXPORTED_DEBT_REMAINS"
        else:
            decision = "PREFIXGRAPH_ISOLATION_BUILDER_SUPPORTED"

    return {
        "schema": "cmpct-v030-prefixgraph-isolation-productization-v2",
        "source_commit": _head(),
        "preregistration": PREREG,
        "supersedes_preregistration": "docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_PRODUCTIZATION_PREREG.md",
        "causal_prerequisite": "docs/v030-rnd/R25_SHIFTED_SERIALIZED_METADATA_CAUSAL_V2_RESULT.md",
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "fixed_mtime_ns": FIXED_MTIME_NS,
        "r24_preflight": {"bytes": preflight_bytes, "sha256": preflight_sha},
        "run_order": [list(order) for order in ORDER],
        "rows": rows,
        "hostile_rows": hostile_rows,
        "arm_counts": counts,
        "deterministic": deterministic,
        "summaries": summaries,
        "derived": derived,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "fixture_intervention": "atime+mtime-only",
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "minimum_rss_reduction": 0.20,
            "maximum_wall_ratio": 1.10,
            "maximum_size_penalty_bytes": 8192,
            "maximum_size_penalty_ratio": 0.005,
            "r24_exact_bytes": R24_BYTES,
            "r24_exact_sha256": R24_SHA256,
            "prefixgraph_selected_required": True,
            "exactly_one_level15_child_required": True,
            "child_dead_before_g04_required": True,
            "hostile_helper_fail_closed_required": True,
            "release_thresholds_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-productization-v2-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-productization-v2.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "r24_preflight", "summaries", "derived", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("PrefixGraph isolation Builder productization v2 evidence invalid")


if __name__ == "__main__":
    main()
