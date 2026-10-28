from __future__ import annotations

"""Measure whether concurrent G0-G4 + PrefixGraph construction owns release-product peak RSS.

The promoted release-candidate tournament overlaps the two independent complete-artifact builders whenever
PrefixGraph is structurally eligible. That overlap is byte-neutral, but the current runtime authority shows a
large pack-RSS regression (especially Shifted). This fresh-process A/B compares the exact shipping schedule with
an otherwise identical serial inter-candidate schedule. It does not cancel either candidate, alter admission,
change candidate-internal bounded parallelism, or claim release credit.
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
WORKER = ROOT / "benchmarks" / "v030_r25_candidate_overlap_rss_worker.py"
ROUNDS = 2
ORDER = (("shipping", "serial-r25"), ("serial-r25", "shipping"))
TARGETS = (
    ("resemblance_hostile_v1", "01_shifted_versions"),
    ("neutral_hostile_v1", "09_ml_artifacts"),
)
MIN_SHIFTED_RSS_REDUCTION = 0.20
MAX_WALL_REGRESSION_RATIO = 1.05


def _run_worker(mode: str, source: Path, archive: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run(
        [
            sys.executable,
            str(WORKER),
            "--mode", mode,
            "--source", str(source),
            "--archive", str(archive),
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"r25-overlap RSS worker produced no JSON for {mode}: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []

    for suite, name in TARGETS:
        source = roots[(suite, name)]
        repetitions = []
        reference_identity = None
        for round_index, order in enumerate(ORDER):
            measured = {}
            for mode in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{round_index}-{mode}.cmpct"
                receipt = _run_worker(mode, source, archive)
                measured[mode] = receipt
                identity = (
                    str(receipt["archive_sha256"]),
                    int(receipt["archive_bytes"]),
                    str(receipt["tree_sha256"]),
                )
                if reference_identity is None:
                    reference_identity = identity
                elif identity != reference_identity:
                    raise RuntimeError(
                        f"r25 candidate schedule changed product identity for {suite}/{name}: "
                        f"{identity!r} != {reference_identity!r}"
                    )
            shipping = measured["shipping"]
            serial = measured["serial-r25"]
            repetitions.append({
                "round": round_index,
                "execution_order": list(order),
                "shipping": shipping,
                "serial_r25": serial,
                "serial_to_shipping_wall_ratio": float(serial["wall_s"]) / max(float(shipping["wall_s"]), 1e-9),
                "serial_to_shipping_incremental_rss_ratio": float(serial["incremental_peak_rss_kib"]) /
                    max(float(shipping["incremental_peak_rss_kib"]), 1.0),
            })

        ship_wall = statistics.median(float(r["shipping"]["wall_s"]) for r in repetitions)
        serial_wall = statistics.median(float(r["serial_r25"]["wall_s"]) for r in repetitions)
        ship_rss = statistics.median(float(r["shipping"]["incremental_peak_rss_kib"]) for r in repetitions)
        serial_rss = statistics.median(float(r["serial_r25"]["incremental_peak_rss_kib"]) for r in repetitions)
        rows.append({
            "suite": suite,
            "name": name,
            "archive_sha256": str(reference_identity[0]),
            "archive_bytes": int(reference_identity[1]),
            "tree_sha256": str(reference_identity[2]),
            "repetitions": repetitions,
            "shipping_median_wall_s": ship_wall,
            "serial_r25_median_wall_s": serial_wall,
            "shipping_median_incremental_peak_rss_kib": int(ship_rss),
            "serial_r25_median_incremental_peak_rss_kib": int(serial_rss),
            "wall_ratio_serial_to_shipping": serial_wall / max(ship_wall, 1e-9),
            "rss_ratio_serial_to_shipping": serial_rss / max(ship_rss, 1.0),
            "rss_reduction_fraction": 1.0 - serial_rss / max(ship_rss, 1.0),
        })

    shifted = next(row for row in rows if (row["suite"], row["name"]) == TARGETS[0])
    exact_identity = all(
        len({rep["shipping"]["archive_sha256"] for rep in row["repetitions"]}
            | {rep["serial_r25"]["archive_sha256"] for rep in row["repetitions"]}) == 1
        for row in rows
    )
    promotion_signal = (
        exact_identity
        and float(shifted["rss_reduction_fraction"]) >= MIN_SHIFTED_RSS_REDUCTION
        and float(shifted["wall_ratio_serial_to_shipping"]) <= MAX_WALL_REGRESSION_RATIO
    )
    return {
        "schema": "cmpct-v030-r25-candidate-overlap-rss-v1",
        "rounds": ROUNDS,
        "targets": [list(item) for item in TARGETS],
        "rows": rows,
        "contract": {
            "archive_bytes_changed": False,
            "selector_changed": False,
            "candidate_admission_changed": False,
            "candidate_internal_parallelism_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
            "recovery_changed": False,
            "minimum_shifted_rss_reduction_for_promotion_signal": MIN_SHIFTED_RSS_REDUCTION,
            "maximum_shifted_wall_regression_ratio_for_promotion_signal": MAX_WALL_REGRESSION_RATIO,
            "timing_semantics": "fresh-process balanced shipping-vs-serial inter-candidate schedule; strong verification outside pack timer",
        },
        "experiment_valid": bool(exact_identity),
        "promotion_signal": bool(promotion_signal),
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": (
            "Research-only scheduling A/B. A positive signal would authorize a separate memory-aware scheduler "
            "productization attempt only; normal runtime/RSS, external, native/Android and final authority must be re-earned."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-overlap-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-candidate-overlap-rss.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": [
            {
                "target": f"{row['suite']}/{row['name']}",
                "wall_ratio": row["wall_ratio_serial_to_shipping"],
                "rss_ratio": row["rss_ratio_serial_to_shipping"],
                "rss_reduction_fraction": row["rss_reduction_fraction"],
            }
            for row in result["rows"]
        ],
        "promotion_signal": result["promotion_signal"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("r25 candidate-overlap RSS oracle changed product identity")


if __name__ == "__main__":
    main()
