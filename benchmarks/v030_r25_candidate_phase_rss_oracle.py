from __future__ import annotations

"""Attribute release-product r25 RSS to G0-G4 versus PrefixGraph complete-candidate construction.

The preceding shipping-vs-serial A/B falsified inter-candidate overlap as the owner of the peak. This oracle
therefore measures each exact complete candidate in a fresh process and compares its incremental RSS with the
promoted full product. It is diagnostic only: it cannot change admission, scheduling, selection or release state.
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


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [sys.executable, str(WORKER), "--mode", mode, "--source", str(source), "--archive", str(archive)],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"candidate-phase RSS worker produced no JSON for {mode}: {completed.stderr!r}")
    return json.loads(lines[-1])


def _median(rows: list[dict], mode: str, field: str) -> float | None:
    values = [float(row[mode][field]) for row in rows if row.get(mode, {}).get("eligible") is True]
    return statistics.median(values) if values else None


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    output_rows = []
    experiment_valid = True

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        source_tree = PERF._treehash(source)
        repetitions = []
        for round_index, order in enumerate(ORDERS):
            measured: dict[str, dict] = {}
            for mode in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{round_index}-{mode}.cmpct"
                receipt = _run_worker(mode, source, archive)
                measured[mode] = receipt
                if str(receipt.get("tree_sha256")) != source_tree:
                    experiment_valid = False
                if receipt.get("eligible") is True and not archive.is_file():
                    experiment_valid = False
            repetitions.append({"round": round_index, "execution_order": list(order), **measured})

        ship_rss = _median(repetitions, "shipping", "incremental_peak_rss_kib")
        g04_rss = _median(repetitions, "g04", "incremental_peak_rss_kib")
        pg_rss = _median(repetitions, "prefixgraph", "incremental_peak_rss_kib")
        ship_wall = _median(repetitions, "shipping", "wall_s")
        g04_wall = _median(repetitions, "g04", "wall_s")
        pg_wall = _median(repetitions, "prefixgraph", "wall_s")
        if ship_rss is None or g04_rss is None:
            experiment_valid = False

        output_rows.append({
            "suite": suite,
            "name": name,
            "tree_sha256": source_tree,
            "repetitions": repetitions,
            "shipping_median_incremental_peak_rss_kib": None if ship_rss is None else int(ship_rss),
            "g04_median_incremental_peak_rss_kib": None if g04_rss is None else int(g04_rss),
            "prefixgraph_median_incremental_peak_rss_kib": None if pg_rss is None else int(pg_rss),
            "g04_to_shipping_rss_ratio": None if ship_rss in (None, 0) or g04_rss is None else g04_rss / ship_rss,
            "prefixgraph_to_shipping_rss_ratio": None if ship_rss in (None, 0) or pg_rss is None else pg_rss / ship_rss,
            "shipping_median_wall_s": ship_wall,
            "g04_median_wall_s": g04_wall,
            "prefixgraph_median_wall_s": pg_wall,
            "g04_to_shipping_wall_ratio": None if ship_wall in (None, 0) or g04_wall is None else g04_wall / ship_wall,
            "prefixgraph_to_shipping_wall_ratio": None if ship_wall in (None, 0) or pg_wall is None else pg_wall / ship_wall,
        })

    return {
        "schema": "cmpct-v030-r25-candidate-phase-rss-v1",
        "targets": [list(item) for item in TARGETS],
        "orders": [list(item) for item in ORDERS],
        "rows": output_rows,
        "contract": {
            "fresh_process_per_measurement": True,
            "strong_verification_outside_pack_timer": True,
            "candidate_bytes_are_not_combined_or_credited": True,
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
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": (
            "Diagnostic ownership evidence only. Candidate RSS or wall-time ratios cannot authorize cancellation, "
            "selection, promotion or release; any subsequent optimization must preserve exact normal authorities."
        ),
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
        "rows": [{
            "target": f"{row['suite']}/{row['name']}",
            "g04_rss_ratio": row["g04_to_shipping_rss_ratio"],
            "prefixgraph_rss_ratio": row["prefixgraph_to_shipping_rss_ratio"],
            "g04_wall_ratio": row["g04_to_shipping_wall_ratio"],
            "prefixgraph_wall_ratio": row["prefixgraph_to_shipping_wall_ratio"],
        } for row in result["rows"]],
        "experiment_valid": result["experiment_valid"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("r25 candidate-phase RSS ownership evidence is invalid")


if __name__ == "__main__":
    main()
