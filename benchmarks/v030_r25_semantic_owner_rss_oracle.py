from __future__ import annotations

"""Superseding candidate-family RSS oracle using the exact canonical semantic owners.

V1 produced valid measurements but an invalid ownership interpretation because its isolated PrefixGraph arm used
``entropygraph_v030_prefixgraph_parallel`` rather than the private canonical PrefixGraph clone bound to shipping.
This v2 instrument keeps the same fresh-process and two-order measurement boundary while invoking only semantic
owners obtained through ``canonical.RC``.  It is diagnostic only and grants no release credit.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

from benchmarks import v030_release_performance as PERF
from experiments import entropygraph_v030_canonical_final as CANONICAL

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_semantic_owner_rss_worker.py"
ORDERS = (("shipping", "g04", "prefixgraph"), ("prefixgraph", "g04", "shipping"))
TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
SUPERSEDES = {
    "record": "docs/v030-rnd/R25_CANDIDATE_PHASE_RSS_RESULT.md",
    "v1_source": "c2bbfdce215113790124c01fb96f69bf09b8962e",
    "v1_workflow_run": 33589815780,
    "v1_artifact_id": 9831560776,
    "reason": "v1 isolated PrefixGraph arm used the parallel research wrapper rather than canonical.RC.PG",
}


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False, capture_output=True, text=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or not lines:
        return {
            "mode": mode, "eligible": False, "worker_failed": True, "returncode": int(completed.returncode),
            "command": command, "stdout": completed.stdout, "stderr": completed.stderr,
            "archive_exists": archive.is_file(),
            "failure": "worker-failed" if completed.returncode else "worker-completed-without-json",
        }
    try:
        receipt = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {
            "mode": mode, "eligible": False, "worker_failed": True, "returncode": 0, "command": command,
            "stdout": completed.stdout, "stderr": completed.stderr, "archive_exists": archive.is_file(),
            "failure": f"invalid-json:{exc}",
        }
    receipt["worker_failed"] = False
    receipt["returncode"] = 0
    return receipt


def _identity_valid(mode: str, receipt: dict, source_tree: str, archive: Path) -> bool:
    if receipt.get("worker_failed") is True or str(receipt.get("research_tree_sha256") or "") != source_tree:
        return False
    owners = receipt.get("semantic_owners") or {}
    if owners.get("identity_exact") is not True:
        return False
    if owners.get("rc_pg_module") != "experiments._v030_canonical_prefixgraph":
        return False
    if owners.get("rc_g04_module") != "experiments._v030_canonical_shared_portfolio":
        return False
    if receipt.get("eligible") is not True:
        return mode == "prefixgraph" and bool(receipt.get("reject_reason")) and not archive.exists()
    if not archive.is_file():
        return False
    expected = str(receipt.get("expected_verification_tree_sha256") or "")
    verified = str(receipt.get("verified_tree_sha256") or "")
    return bool(expected) and verified == expected and str(receipt.get("tree_sha256") or "") == expected


def _median(repetitions: list[dict], mode: str, field: str) -> float | None:
    values = [float(rep[mode][field]) for rep in repetitions if rep.get(mode, {}).get("eligible") is True]
    return statistics.median(values) if values else None


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []
    failures = []
    experiment_valid = True

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        source_tree = str(CANONICAL.RC.treehash(source))
        repetitions = []
        for round_index, order in enumerate(ORDERS):
            measured = {}
            for mode in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{round_index}-{mode}.cmpct"
                receipt = _run_worker(mode, source, archive)
                measured[mode] = receipt
                if receipt.get("worker_failed") is True or not _identity_valid(mode, receipt, source_tree, archive):
                    experiment_valid = False
                    failures.append({"suite": suite, "name": name, "round": round_index, **receipt})
            repetitions.append({"round": round_index, "execution_order": list(order), **measured})

        ship_peak = _median(repetitions, "shipping", "peak_rss_kib")
        g04_peak = _median(repetitions, "g04", "peak_rss_kib")
        pg_peak = _median(repetitions, "prefixgraph", "peak_rss_kib")
        ship_inc = _median(repetitions, "shipping", "incremental_peak_rss_kib")
        g04_inc = _median(repetitions, "g04", "incremental_peak_rss_kib")
        pg_inc = _median(repetitions, "prefixgraph", "incremental_peak_rss_kib")
        ship_wall = _median(repetitions, "shipping", "wall_s")
        g04_wall = _median(repetitions, "g04", "wall_s")
        pg_wall = _median(repetitions, "prefixgraph", "wall_s")
        if ship_peak is None or g04_peak is None:
            experiment_valid = False
        rows.append({
            "suite": suite, "name": name, "tree_sha256": source_tree, "repetitions": repetitions,
            "shipping_median_peak_rss_kib": None if ship_peak is None else int(ship_peak),
            "g04_median_peak_rss_kib": None if g04_peak is None else int(g04_peak),
            "prefixgraph_median_peak_rss_kib": None if pg_peak is None else int(pg_peak),
            "g04_to_shipping_peak_rss_ratio": None if not ship_peak or g04_peak is None else g04_peak / ship_peak,
            "prefixgraph_to_shipping_peak_rss_ratio": None if not ship_peak or pg_peak is None else pg_peak / ship_peak,
            "shipping_median_incremental_peak_rss_kib": None if ship_inc is None else int(ship_inc),
            "g04_median_incremental_peak_rss_kib": None if g04_inc is None else int(g04_inc),
            "prefixgraph_median_incremental_peak_rss_kib": None if pg_inc is None else int(pg_inc),
            "g04_to_shipping_rss_ratio": None if not ship_inc or g04_inc is None else g04_inc / ship_inc,
            "prefixgraph_to_shipping_rss_ratio": None if not ship_inc or pg_inc is None else pg_inc / ship_inc,
            "shipping_median_wall_s": ship_wall,
            "g04_median_wall_s": g04_wall,
            "prefixgraph_median_wall_s": pg_wall,
            "g04_to_shipping_wall_ratio": None if not ship_wall or g04_wall is None else g04_wall / ship_wall,
            "prefixgraph_to_shipping_wall_ratio": None if not ship_wall or pg_wall is None else pg_wall / ship_wall,
        })

    return {
        "schema": "cmpct-v030-r25-semantic-owner-rss-v2",
        "source_commit": _source_commit(),
        "supersedes": SUPERSEDES,
        "targets": [list(x) for x in TARGETS],
        "orders": [list(x) for x in ORDERS],
        "rows": rows,
        "worker_failures": failures,
        "contract": {
            "fresh_process_per_measurement": True,
            "exact_canonical_semantic_owner_identity_required": True,
            "strong_verification_outside_pack_timer": True,
            "candidate_bytes_are_not_combined_or_credited": True,
            "release_boundary_attribution_uses_total_fresh_process_peak_rss": True,
            "baseline_subtracted_ru_maxrss_is_diagnostic_only": True,
            "selector_changed": False,
            "admission_changed": False,
            "scheduling_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
            "recovery_changed": False,
        },
        "experiment_valid": bool(experiment_valid),
        "promotion_signal": False,
        "release_credit": False,
        "claim_boundary": (
            "Diagnostic causal ownership only. V2 supersedes v1 interpretation because every isolated arm must be "
            "the exact private canonical semantic owner shipping invokes."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-semantic-owner-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-semantic-owner-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_commit": result["source_commit"],
        "experiment_valid": result["experiment_valid"],
        "rows": [{
            "target": f"{row['suite']}/{row['name']}",
            "g04_peak_ratio": row["g04_to_shipping_peak_rss_ratio"],
            "prefixgraph_peak_ratio": row["prefixgraph_to_shipping_peak_rss_ratio"],
            "g04_wall_ratio": row["g04_to_shipping_wall_ratio"],
            "prefixgraph_wall_ratio": row["prefixgraph_to_shipping_wall_ratio"],
        } for row in result["rows"]],
        "failures": len(result["worker_failures"]),
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("semantic-owner RSS v2 evidence invalid; inspect durable worker_failures")


if __name__ == "__main__":
    main()
