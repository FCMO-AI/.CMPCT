from __future__ import annotations

"""Attribute release-product r25 RSS to G0-G4 versus PrefixGraph complete-candidate construction.

The preceding shipping-vs-serial A/B falsified inter-candidate overlap as the owner of the peak. The exact-head
product-phase oracle then falsified canonical profile/manifest capture alone as the dominant RSS owner on shifted,
logs, and ML: profile capture did not rise above the matched fresh-process import baseline while the complete product
did. This oracle therefore measures each exact complete candidate in a fresh process and compares its RSS with the
promoted full product. Total fresh-process peak RSS is the decisive ownership boundary because that is what the
release gate charges. Baseline-subtracted ru_maxrss remains visible only as a diagnostic: ru_maxrss is a high-water
mark, not an additive allocation counter. This oracle is diagnostic only and cannot change admission, scheduling,
selection or release state.

Worker failures are evidence too. A failed child process is retained verbatim in the durable JSON instead of being
lost behind CalledProcessError; the oracle then fails closed with experiment_valid=false.
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
from experiments import entropygraph_v030_release_candidate as CAND

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_phase_rss_worker.py"
ORDERS = (
    ("shipping", "g04", "prefixgraph"),
    ("prefixgraph", "g04", "shipping"),
)
TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
CAUSAL_PREDECESSOR = {
    "record": "docs/v030-rnd/R25_PRODUCT_PHASE_RSS_RESULT.md",
    "source_head": "86d6407816a71eb35df288b9b0bb91ce10f73f08",
    "workflow_run": 33587322779,
    "artifact_id": 9830647880,
    "scoped_negative_constraint": (
        "canonical profile/manifest capture alone did not raise total fresh-process peak RSS above the matched "
        "import baseline on shifted, logs, or ML; candidate construction is the next unresolved ownership layer"
    ),
}


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    command = [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False, capture_output=True, text=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0:
        return {"mode": mode, "eligible": False, "worker_failed": True, "returncode": int(completed.returncode),
                "command": command, "stdout": completed.stdout, "stderr": completed.stderr,
                "archive_exists": archive.is_file()}
    if not lines:
        return {"mode": mode, "eligible": False, "worker_failed": True, "returncode": 0, "command": command,
                "stdout": completed.stdout, "stderr": completed.stderr, "archive_exists": archive.is_file(),
                "failure": "worker completed without a JSON receipt"}
    try:
        receipt = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        return {"mode": mode, "eligible": False, "worker_failed": True, "returncode": 0, "command": command,
                "stdout": completed.stdout, "stderr": completed.stderr, "archive_exists": archive.is_file(),
                "failure": f"invalid final JSON receipt: {exc}"}
    receipt["worker_failed"] = False
    receipt["returncode"] = 0
    return receipt


def _receipt_identity_valid(mode: str, receipt: dict, source_tree: str, archive: Path) -> bool:
    if receipt.get("worker_failed") is True or str(receipt.get("research_tree_sha256") or "") != source_tree:
        return False
    eligible = receipt.get("eligible") is True
    if not eligible:
        return mode == "prefixgraph" and bool(receipt.get("reject_reason")) and not archive.is_file()
    if not archive.is_file():
        return False
    expected = str(receipt.get("expected_verification_tree_sha256") or "")
    verified = str(receipt.get("verified_tree_sha256") or receipt.get("tree_sha256") or "")
    observed = str(receipt.get("tree_sha256") or "")
    return bool(expected) and verified == expected and observed == expected


def _median(rows: list[dict], mode: str, field: str) -> float | None:
    values = [float(row[mode][field]) for row in rows if row.get(mode, {}).get("eligible") is True]
    return statistics.median(values) if values else None


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    output_rows = []
    experiment_valid = True
    worker_failures: list[dict] = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        source_tree = CAND.treehash(source)
        repetitions = []
        for round_index, order in enumerate(ORDERS):
            measured: dict[str, dict] = {}
            for mode in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{round_index}-{mode}.cmpct"
                receipt = _run_worker(mode, source, archive)
                measured[mode] = receipt
                if receipt.get("worker_failed") is True:
                    experiment_valid = False
                    worker_failures.append({"suite": suite, "name": name, "round": round_index, **receipt})
                    continue
                if not _receipt_identity_valid(mode, receipt, source_tree, archive):
                    experiment_valid = False
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

        output_rows.append({
            "suite": suite, "name": name, "tree_sha256": source_tree, "repetitions": repetitions,
            "shipping_median_peak_rss_kib": None if ship_peak is None else int(ship_peak),
            "g04_median_peak_rss_kib": None if g04_peak is None else int(g04_peak),
            "prefixgraph_median_peak_rss_kib": None if pg_peak is None else int(pg_peak),
            "g04_to_shipping_peak_rss_ratio": None if ship_peak in (None, 0) or g04_peak is None else g04_peak / ship_peak,
            "prefixgraph_to_shipping_peak_rss_ratio": None if ship_peak in (None, 0) or pg_peak is None else pg_peak / ship_peak,
            "shipping_median_incremental_peak_rss_kib": None if ship_inc is None else int(ship_inc),
            "g04_median_incremental_peak_rss_kib": None if g04_inc is None else int(g04_inc),
            "prefixgraph_median_incremental_peak_rss_kib": None if pg_inc is None else int(pg_inc),
            "g04_to_shipping_rss_ratio": None if ship_inc in (None, 0) or g04_inc is None else g04_inc / ship_inc,
            "prefixgraph_to_shipping_rss_ratio": None if ship_inc in (None, 0) or pg_inc is None else pg_inc / ship_inc,
            "shipping_median_wall_s": ship_wall, "g04_median_wall_s": g04_wall, "prefixgraph_median_wall_s": pg_wall,
            "g04_to_shipping_wall_ratio": None if ship_wall in (None, 0) or g04_wall is None else g04_wall / ship_wall,
            "prefixgraph_to_shipping_wall_ratio": None if ship_wall in (None, 0) or pg_wall is None else pg_wall / ship_wall,
        })

    return {
        "schema": "cmpct-v030-r25-candidate-phase-rss-v1", "source_commit": _source_commit(),
        "causal_predecessor": CAUSAL_PREDECESSOR,
        "targets": [list(item) for item in TARGETS], "orders": [list(item) for item in ORDERS], "rows": output_rows,
        "worker_failures": worker_failures,
        "contract": {
            "fresh_process_per_measurement": True, "worker_failure_output_is_durable": True,
            "strong_verification_outside_pack_timer": True, "mode_specific_identity_domains_preserved": True,
            "structural_ineligibility_is_not_reclassified_as_failure": True,
            "candidate_bytes_are_not_combined_or_credited": True,
            "release_boundary_attribution_uses_total_fresh_process_peak_rss": True,
            "baseline_subtracted_ru_maxrss_is_diagnostic_only": True,
            "selector_changed": False, "admission_changed": False, "scheduling_changed": False,
            "grammar_changed": False, "integrity_changed": False, "locality_limit_changed": False,
            "decode_unit_limit_changed": False, "recovery_changed": False,
        },
        "experiment_valid": bool(experiment_valid), "promotion_signal": False, "selector_change": False,
        "release_credit": False,
        "claim_boundary": "Diagnostic ownership evidence only. Total fresh-process peak RSS is the release-boundary ownership signal; baseline-subtracted ru_maxrss is diagnostic only. Candidate ratios cannot authorize cancellation, selection, promotion or release.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-phase-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-phase-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_commit": result["source_commit"],
        "rows": [{
            "target": f"{row['suite']}/{row['name']}",
            "g04_peak_rss_ratio": row["g04_to_shipping_peak_rss_ratio"],
            "prefixgraph_peak_rss_ratio": row["prefixgraph_to_shipping_peak_rss_ratio"],
            "g04_incremental_rss_ratio_diagnostic": row["g04_to_shipping_rss_ratio"],
            "prefixgraph_incremental_rss_ratio_diagnostic": row["prefixgraph_to_shipping_rss_ratio"],
            "g04_wall_ratio": row["g04_to_shipping_wall_ratio"],
            "prefixgraph_wall_ratio": row["prefixgraph_to_shipping_wall_ratio"],
        } for row in result["rows"]],
        "worker_failures": len(result["worker_failures"]), "experiment_valid": result["experiment_valid"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        for failure in result["worker_failures"]:
            print(f"worker failure {failure['suite']}/{failure['name']} round={failure['round']} mode={failure['mode']} rc={failure.get('returncode')}\nstdout:\n{failure.get('stdout', '')}\nstderr:\n{failure.get('stderr', '')}", file=sys.stderr, flush=True)
        raise SystemExit("r25 candidate-phase RSS ownership evidence is invalid")


if __name__ == "__main__":
    main()
