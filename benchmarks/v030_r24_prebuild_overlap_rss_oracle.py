from __future__ import annotations

"""Causally isolate the release-product r24-prebuild overlap as a pack-RSS owner.

The runtime authority currently observes a severe pack-RSS regression, especially on Shifted versions. Shipping
starts canonical r24 compression in a background thread while the revision-25 profile tree performs manifest/content
capture. This oracle compares that exact shipping schedule with a fresh-process serial schedule that restores the
same r24 builder and the same canonical profile-tree implementation but does not overlap them.

The experiment changes no archive bytes, selector, grammar, integrity, locality, recovery or memory limit. It is
research-only and cannot earn release credit. Its purpose is to decide whether the overlap is a causal memory owner
before changing a schedule that was originally introduced to save creation time.
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
WORKER = ROOT / "benchmarks" / "v030_r24_prebuild_overlap_rss_worker.py"
ROUNDS = 2
ORDER = (("shipping", "serial-r24"), ("serial-r24", "shipping"))
SHIFTED_KEY = ("resemblance_hostile_v1", "01_shifted_versions")
MIN_CAUSAL_RSS_REDUCTION = 0.20


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
        raise RuntimeError(f"r24-overlap RSS worker produced no JSON for {mode}: {completed.stderr!r}")
    return json.loads(lines[-1])


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    rows = []

    for suite, name in PERF.TARGETS:
        source = roots[(suite, name)]
        repetitions = []
        reference_sha = None
        reference_bytes = None
        reference_tree = None
        for round_index, order in enumerate(ORDER):
            measured = {}
            for mode in order:
                archive = work_root / "archives" / f"{suite}-{name}-r{round_index}-{mode}.cmpct"
                receipt = _run_worker(mode, source, archive)
                measured[mode] = receipt
                archive_sha = str(receipt["archive_sha256"])
                archive_bytes = int(receipt["archive_bytes"])
                tree = str(receipt["tree_sha256"])
                if reference_sha is None:
                    reference_sha, reference_bytes, reference_tree = archive_sha, archive_bytes, tree
                elif (archive_sha, archive_bytes, tree) != (reference_sha, reference_bytes, reference_tree):
                    raise RuntimeError(
                        f"r24-overlap schedule changed product identity for {suite}/{name}: "
                        f"{(archive_sha, archive_bytes, tree)!r} != {(reference_sha, reference_bytes, reference_tree)!r}"
                    )
            shipping = measured["shipping"]
            serial = measured["serial-r24"]
            repetitions.append({
                "round": round_index,
                "execution_order": list(order),
                "shipping": shipping,
                "serial_r24": serial,
                "serial_to_shipping_wall_ratio": float(serial["wall_s"]) / max(float(shipping["wall_s"]), 1e-9),
                "serial_to_shipping_rss_ratio": float(serial["peak_rss_kib"]) / max(float(shipping["peak_rss_kib"]), 1),
            })

        shipping_wall = statistics.median(float(r["shipping"]["wall_s"]) for r in repetitions)
        serial_wall = statistics.median(float(r["serial_r24"]["wall_s"]) for r in repetitions)
        shipping_rss = statistics.median(float(r["shipping"]["peak_rss_kib"]) for r in repetitions)
        serial_rss = statistics.median(float(r["serial_r24"]["peak_rss_kib"]) for r in repetitions)
        rows.append({
            "suite": suite,
            "name": name,
            "archive_bytes": int(reference_bytes),
            "archive_sha256": str(reference_sha),
            "tree_sha256": str(reference_tree),
            "repetitions": repetitions,
            "shipping_median_wall_s": float(shipping_wall),
            "serial_r24_median_wall_s": float(serial_wall),
            "shipping_median_peak_rss_kib": int(shipping_rss),
            "serial_r24_median_peak_rss_kib": int(serial_rss),
            "wall_ratio_serial_to_shipping": float(serial_wall / max(shipping_wall, 1e-9)),
            "rss_ratio_serial_to_shipping": float(serial_rss / max(shipping_rss, 1.0)),
            "rss_reduction_fraction": float(1.0 - serial_rss / max(shipping_rss, 1.0)),
        })

    shifted = next(row for row in rows if (row["suite"], row["name"]) == SHIFTED_KEY)
    exact_identity = all(
        len({rep["shipping"]["archive_sha256"] for rep in row["repetitions"]}
            | {rep["serial_r24"]["archive_sha256"] for rep in row["repetitions"]}) == 1
        for row in rows
    )
    causal_signal = exact_identity and float(shifted["rss_reduction_fraction"]) >= MIN_CAUSAL_RSS_REDUCTION
    return {
        "schema": "cmpct-v030-r24-prebuild-overlap-rss-v1",
        "rounds": ROUNDS,
        "targets": [list(item) for item in PERF.TARGETS],
        "rows": rows,
        "contract": {
            "archive_bytes_changed": False,
            "selector_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
            "recovery_changed": False,
            "minimum_shifted_rss_reduction_for_causal_signal": MIN_CAUSAL_RSS_REDUCTION,
            "timing_semantics": "fresh-process balanced shipping-vs-serial schedule; strong verification/tree hashing outside pack timer",
        },
        "experiment_valid": bool(exact_identity),
        "causal_signal": bool(causal_signal),
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": (
            "Research-only scheduling A/B. A causal signal means the r24/profile-tree overlap materially owns the "
            "Shifted pack-RSS increase; it does not authorize a shipping schedule change until creation-time and "
            "the frozen <=1.25x v0.29 RSS law are re-earned on the normal runtime authority."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-prebuild-overlap-rss-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-prebuild-overlap-rss.json"))
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
        "causal_signal": result["causal_signal"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("r24 prebuild-overlap RSS oracle changed product identity")


if __name__ == "__main__":
    main()
