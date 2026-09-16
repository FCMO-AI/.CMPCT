from __future__ import annotations

"""Frozen complete-product A/B/C for PrefixGraph isolation create-debt rehabilitation."""

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from benchmarks import v030_release_generalization as GENERAL
from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_release_product as PRODUCT

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_prefixgraph_isolation_level15_debt_worker.py"
TARGET = ("resemblance_hostile_v1", "01_shifted_versions")
PREREG = "docs/v030-rnd/R25_PREFIXGRAPH_ISOLATION_LEVEL15_DEBT_REHAB_PREREG.md"
MODES = ("shipping-l19", "isolated-l19", "isolated-l15")
ORDER = (
    ("shipping-l19", "isolated-l19", "isolated-l15"),
    ("isolated-l15", "isolated-l19", "shipping-l19"),
)


def _head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.returncode or not lines:
        return {
            "worker_failed": True,
            "mode": mode,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    try:
        data = json.loads(lines[-1])
    except Exception as exc:
        return {
            "worker_failed": True,
            "mode": mode,
            "returncode": 0,
            "failure": f"json:{exc}",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    data["worker_failed"] = False
    return data


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    work_root = Path(work_root)
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    accepted = GENERAL._accepted_v029_rows()
    source = PERF._build_corpora(work_root / "corpora")[TARGET]
    expected_historical_tree = str(accepted[TARGET]["tree_sha256"])
    historical_tree = str(GENERAL._historical_treehash(source))
    product_tree = str(PRODUCT.treehash(source))
    if historical_tree != expected_historical_tree:
        raise RuntimeError("isolation-debt source drifted from accepted repaired Shifted authority")

    rows: list[dict] = []
    failures: list[dict] = []
    counts = {mode: 0 for mode in MODES}

    for round_index, modes in enumerate(ORDER):
        for position, mode in enumerate(modes):
            counts[mode] += 1
            archive = work_root / "archives" / f"round{round_index}-{position}-{mode}.cmpct"
            archive.parent.mkdir(parents=True, exist_ok=True)
            data = _run(mode, source, archive)
            data["round_index"] = round_index
            data["position"] = position
            rows.append(data)
            owners = data.get("semantic_owners") or {}
            expected_level = 15 if mode == "isolated-l15" else 19
            ok = (
                not data.get("worker_failed")
                and data.get("mode") == mode
                and int(data.get("prefix_level", -1)) == expected_level
                and data.get("expected_verification_tree_sha256") == product_tree
                and data.get("tree_sha256") == product_tree
                and data.get("verification_identity_domain") == "canonical-filesystem-user-tree-v1"
                and data.get("research_identity_domain") == "research-content-tree-v1"
                and owners.get("identity_exact") is True
                and owners.get("pg") == "experiments._v030_canonical_prefixgraph"
                and owners.get("g04") == "experiments._v030_canonical_shared_portfolio"
                and owners.get("reader") == "experiments._v030_canonical_release_reader_policy"
                and data.get("executor_restored") is True
                and data.get("r24_product_bytes") is not None
                and data.get("r25_product_bytes") is not None
                and data.get("selected") == "prefixgraph"
                and int(data.get("tree_peak_rss_kib", 0)) > 0
                and int(data.get("tree_samples", 0)) >= 100
                and data.get("tree_sampler_errors") == []
                and float(data.get("tree_sampler_interval_s", 1.0)) <= 0.01
            )
            if mode == "shipping-l19":
                ok = ok and (
                    data.get("intercepted_prefixgraph_executor_constructions") == 0
                    and data.get("intercepted_prefixgraph_submissions") == 0
                    and data.get("isolated_children_launched") == 0
                    and data.get("isolated_child_returncodes") == []
                    and data.get("isolated_child_levels") == []
                )
            else:
                ok = ok and (
                    data.get("intercepted_prefixgraph_executor_constructions") == 1
                    and data.get("intercepted_prefixgraph_submissions") == 1
                    and data.get("isolated_children_launched") == 1
                    and data.get("isolated_child_returncodes") == [0]
                    and data.get("isolated_child_levels") == [expected_level]
                    and len(data.get("isolated_child_archive_bytes") or []) == 1
                    and len(data.get("isolated_child_archive_sha256") or []) == 1
                )
            if not ok:
                failures.append({"round": round_index, "position": position, **data})

    summaries: dict[str, dict] = {}
    deterministic: dict[str, bool] = {}
    for mode in MODES:
        mode_rows = [row for row in rows if row.get("mode") == mode and not row.get("worker_failed")]
        identities = {
            tuple(row.get(key) for key in (
                "archive_bytes", "archive_sha256", "tree_sha256", "selected", "format_revision",
                "r24_product_bytes", "r25_product_bytes",
            ))
            for row in mode_rows
        }
        deterministic[mode] = len(mode_rows) == 2 and len(identities) == 1
        if len(mode_rows) != 2:
            continue
        summaries[mode] = {
            "archive_bytes": int(mode_rows[0]["archive_bytes"]),
            "archive_sha256": mode_rows[0]["archive_sha256"],
            "r24_product_bytes": int(mode_rows[0]["r24_product_bytes"]),
            "r25_product_bytes": int(mode_rows[0]["r25_product_bytes"]),
            "median_tree_peak_rss_kib": _median(mode_rows, "tree_peak_rss_kib"),
            "median_parent_peak_ru_maxrss_kib": _median(mode_rows, "parent_peak_ru_maxrss_kib"),
            "median_wall_s": _median(mode_rows, "wall_s"),
            "median_tree_samples": _median(mode_rows, "tree_samples"),
            "max_tree_peak_processes": max(int(row["tree_peak_processes"]) for row in mode_rows),
            "deterministic": deterministic[mode],
        }

    exact_neutral_isolation = False
    if "shipping-l19" in summaries and "isolated-l19" in summaries:
        a = summaries["shipping-l19"]
        b = summaries["isolated-l19"]
        exact_neutral_isolation = all(a[key] == b[key] for key in (
            "archive_bytes", "archive_sha256", "r24_product_bytes", "r25_product_bytes"
        ))

    valid = (
        not failures
        and counts == {mode: 2 for mode in MODES}
        and set(summaries) == set(MODES)
        and all(deterministic.values())
        and exact_neutral_isolation
    )

    derived: dict[str, float | int | bool] = {}
    decision = "INVALID_CORRECTNESS_OR_CUSTODY"
    if valid:
        shipping = summaries["shipping-l19"]
        isolated19 = summaries["isolated-l19"]
        candidate = summaries["isolated-l15"]
        shipping_peak = float(shipping["median_tree_peak_rss_kib"])
        shipping_wall = float(shipping["median_wall_s"])
        isolated19_wall = float(isolated19["median_wall_s"])
        candidate_peak = float(candidate["median_tree_peak_rss_kib"])
        candidate_wall = float(candidate["median_wall_s"])
        size_penalty = int(candidate["archive_bytes"]) - int(shipping["archive_bytes"])
        size_penalty_ratio = size_penalty / int(shipping["archive_bytes"])
        rss_reduction = 1.0 - candidate_peak / shipping_peak
        wall_vs_shipping = candidate_wall / shipping_wall
        wall_vs_isolated19 = candidate_wall / isolated19_wall
        byte_budget_ok = size_penalty <= 8192 and size_penalty_ratio <= 0.005
        derived = {
            "candidate_tree_peak_reduction_fraction_vs_shipping": rss_reduction,
            "candidate_wall_ratio_vs_shipping": wall_vs_shipping,
            "candidate_wall_ratio_vs_isolated_l19": wall_vs_isolated19,
            "candidate_archive_size_penalty_bytes_vs_shipping": size_penalty,
            "candidate_archive_size_penalty_ratio_vs_shipping": size_penalty_ratio,
            "byte_budget_ok": byte_budget_ok,
            "shipping_vs_isolated_l19_exact": exact_neutral_isolation,
        }
        if (
            rss_reduction >= 0.20
            and wall_vs_shipping <= 1.10
            and wall_vs_isolated19 <= 0.95
            and byte_budget_ok
        ):
            decision = "ISOLATION_LEVEL15_DEBT_REHAB_SUPPORTED"
        elif rss_reduction >= 0.20 and wall_vs_shipping > 1.10:
            decision = "ISOLATION_MEMORY_WIN_CREATE_DEBT_REMAINS"
        elif rss_reduction >= 0.20:
            decision = "ISOLATION_LEVEL15_REHAB_INSUFFICIENT"
        else:
            decision = "ISOLATION_MEMORY_WIN_NOT_PRESERVED"

    return {
        "schema": "cmpct-v030-prefixgraph-isolation-level15-debt-rehab-v1",
        "source_commit": _head(),
        "preregistration": PREREG,
        "target": list(TARGET),
        "accepted_historical_tree_sha256": expected_historical_tree,
        "product_tree_sha256": product_tree,
        "run_order": [list(x) for x in ORDER],
        "rows": rows,
        "arm_counts": counts,
        "deterministic": deterministic,
        "summaries": summaries,
        "derived": derived,
        "decision": decision,
        "experiment_valid": valid,
        "worker_failures": failures,
        "release_credit": False,
        "contract": {
            "whole_process_tree_rss_decisive": True,
            "parent_ru_maxrss_diagnostic_only": True,
            "sampler_interval_s_max": 0.01,
            "min_samples_per_row": 100,
            "shipping_isolated_l19_exact_identity_required": True,
            "isolated_l15_tree_identity_and_determinism_required": True,
            "minimum_candidate_rss_reduction": 0.20,
            "maximum_candidate_wall_ratio_vs_shipping": 1.10,
            "maximum_candidate_wall_ratio_vs_isolated_l19": 0.95,
            "maximum_size_penalty_bytes": 8192,
            "maximum_size_penalty_ratio": 0.005,
            "production_source_changed": False,
            "release_thresholds_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-level15-debt-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-prefixgraph-isolation-level15-debt.json"))
    args = parser.parse_args()
    data = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: data[key] for key in (
        "source_commit", "experiment_valid", "summaries", "derived", "decision")}, indent=2), flush=True)
    if not data["experiment_valid"]:
        raise SystemExit("PrefixGraph isolation level-15 debt rehabilitation evidence invalid")


if __name__ == "__main__":
    main()
