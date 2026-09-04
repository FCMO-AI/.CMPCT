from __future__ import annotations

"""Causally test the r24/PrefixGraph interaction as a full-product RSS owner.

Two exact-byte diagnostics have already falsified the obvious one-variable changes:
serializing the r24 prebuild did not lower full-product RSS, while reducing PrefixGraph
from four to two workers cut isolated PrefixGraph RSS roughly in half but barely moved
the full-product peak. Those failures can coexist if the remaining large phase still
masks the changed arm. This oracle therefore measures shipping, serial-r24, and the
combined serial-r24 + two-worker PrefixGraph schedule in fresh processes.

No candidate set, serializer, tie law, archive grammar, selector, integrity, locality,
recovery or release threshold changes. This is research-only and cannot earn release
credit. Any useful combined signal still has to re-earn ordinary runtime authority.
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
MODES = ("shipping", "serial-r24", "serial-r24-pg2")
ORDERS = (
    MODES,
    tuple(reversed(MODES)),
)
SHIFTED_KEY = ("resemblance_hostile_v1", "01_shifted_versions")
MIN_CAUSAL_RSS_REDUCTION = 0.12
MAX_WALL_RATIO_FOR_SIGNAL = 1.10


def _source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


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
        raise RuntimeError(f"r24/PrefixGraph RSS worker produced no JSON for {mode}: {completed.stderr!r}")
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
        for round_index, order in enumerate(ORDERS):
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
                if reference_sha is None:
                    reference_sha, reference_bytes, reference_tree = identity
                elif identity != (reference_sha, reference_bytes, reference_tree):
                    raise RuntimeError(
                        f"r24/PrefixGraph schedule changed product identity for {suite}/{name}: "
                        f"{identity!r} != {(reference_sha, reference_bytes, reference_tree)!r}"
                    )
            repetitions.append({
                "round": round_index,
                "execution_order": list(order),
                "shipping": measured["shipping"],
                "serial_r24": measured["serial-r24"],
                "serial_r24_pg2": measured["serial-r24-pg2"],
            })

        def med(mode_key: str, field: str) -> float:
            return float(statistics.median(float(r[mode_key][field]) for r in repetitions))

        shipping_wall = med("shipping", "wall_s")
        serial_wall = med("serial_r24", "wall_s")
        combined_wall = med("serial_r24_pg2", "wall_s")
        shipping_rss = med("shipping", "peak_rss_kib")
        serial_rss = med("serial_r24", "peak_rss_kib")
        combined_rss = med("serial_r24_pg2", "peak_rss_kib")
        rows.append({
            "suite": suite,
            "name": name,
            "archive_bytes": int(reference_bytes),
            "archive_sha256": str(reference_sha),
            "tree_sha256": str(reference_tree),
            "repetitions": repetitions,
            "shipping_median_wall_s": shipping_wall,
            "serial_r24_median_wall_s": serial_wall,
            "serial_r24_pg2_median_wall_s": combined_wall,
            "shipping_median_peak_rss_kib": int(shipping_rss),
            "serial_r24_median_peak_rss_kib": int(serial_rss),
            "serial_r24_pg2_median_peak_rss_kib": int(combined_rss),
            "serial_rss_reduction_fraction": float(1.0 - serial_rss / max(shipping_rss, 1.0)),
            "combined_rss_reduction_fraction": float(1.0 - combined_rss / max(shipping_rss, 1.0)),
            "combined_wall_ratio_to_shipping": float(combined_wall / max(shipping_wall, 1e-9)),
        })

    shifted = next(row for row in rows if (row["suite"], row["name"]) == SHIFTED_KEY)
    exact_identity = all(
        len(
            {rep[key]["archive_sha256"] for rep in row["repetitions"] for key in ("shipping", "serial_r24", "serial_r24_pg2")}
        ) == 1
        for row in rows
    )
    causal_signal = (
        exact_identity
        and float(shifted["combined_rss_reduction_fraction"]) >= MIN_CAUSAL_RSS_REDUCTION
        and float(shifted["combined_wall_ratio_to_shipping"]) <= MAX_WALL_RATIO_FOR_SIGNAL
    )
    return {
        "schema": "cmpct-v030-r24-prefixgraph-combined-rss-v2",
        "source_commit": _source_commit(),
        "rounds": ROUNDS,
        "targets": [list(item) for item in PERF.TARGETS],
        "rows": rows,
        "contract": {
            "archive_bytes_changed": False,
            "candidate_set_changed": False,
            "serializer_changed": False,
            "tie_law_changed": False,
            "selector_changed": False,
            "grammar_changed": False,
            "integrity_changed": False,
            "locality_limit_changed": False,
            "decode_unit_limit_changed": False,
            "recovery_changed": False,
            "production_schedule_changed": False,
            "minimum_shifted_rss_reduction_for_causal_signal": MIN_CAUSAL_RSS_REDUCTION,
            "maximum_shifted_wall_ratio_for_causal_signal": MAX_WALL_RATIO_FOR_SIGNAL,
            "timing_semantics": "fresh-process balanced shipping-vs-serial-vs-combined schedule; strong verification/tree hashing outside pack timer",
        },
        "experiment_valid": bool(exact_identity),
        "causal_signal": bool(causal_signal),
        "selector_change": False,
        "release_credit": False,
        "claim_boundary": (
            "Research-only scheduling interaction A/B. A causal signal only nominates the combined schedule for "
            "ordinary runtime authority; it does not authorize production until frozen create/RSS and all release "
            "invariants are independently re-earned."
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
                "serial_rss_reduction_fraction": row["serial_rss_reduction_fraction"],
                "combined_rss_reduction_fraction": row["combined_rss_reduction_fraction"],
                "combined_wall_ratio_to_shipping": row["combined_wall_ratio_to_shipping"],
            }
            for row in result["rows"]
        ],
        "causal_signal": result["causal_signal"],
    }, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("r24/PrefixGraph combined RSS oracle changed product identity")


if __name__ == "__main__":
    main()
