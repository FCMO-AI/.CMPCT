"""ONE-G0.2 isolated-process RSS probe for generic vs bulk digest observation.

Each measured observer runs in a fresh child process so ru_maxrss is not contaminated by
whichever candidate happened to execute first. This is a resource probe, not a promotion
gate: interpreter/runtime baseline is included in both absolute peaks.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import subprocess
import sys

from benchmarks.one.one_g02_bulk_digest_generalization import (
    compressed_like,
    numeric,
    random_bytes,
    repetitive,
    structured,
)
from experiments.one.morphology_gate import _observe_bulk_digest
from experiments.one.observe import observe

FAMILIES = {
    "numeric": numeric,
    "structured": structured,
    "random": random_bytes,
    "compressed_like": compressed_like,
    "repetitive": repetitive,
}
SIZES = (1024 * 1024, 4 * 1024 * 1024)


def _bulk(data: bytes):
    return _observe_bulk_digest(
        data,
        min_run=8,
        chunk_size=64,
        max_index_entries=1 << 16,
        classifier_bytes=0,
    )


def _worker(mode: str, family: str, size: int) -> None:
    data = FAMILIES[family](size)
    fn = observe if mode == "generic" else _bulk
    result = fn(data)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    print(json.dumps({
        "mode": mode,
        "family": family,
        "size": size,
        "pid": os.getpid(),
        "ru_maxrss_kib": int(usage.ru_maxrss),
        "peak_index_entries": result.stats.peak_index_entries,
        "retained_index_payload_bytes": result.stats.retained_index_payload_bytes,
        "reuse_bytes": result.stats.reuse_opportunity_bytes,
        "run_bytes": result.stats.run_opportunity_bytes,
    }, sort_keys=True))


def _child(mode: str, family: str, size: int) -> dict[str, object]:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "benchmarks.one.one_g02_bulk_digest_rss_probe",
            "--worker",
            "--mode", mode,
            "--family", family,
            "--size", str(size),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--mode", choices=("generic", "bulk"))
    parser.add_argument("--family", choices=tuple(FAMILIES))
    parser.add_argument("--size", type=int)
    args = parser.parse_args()

    if args.worker:
        if args.mode is None or args.family is None or args.size is None:
            parser.error("worker mode requires --mode, --family, and --size")
        _worker(args.mode, args.family, args.size)
        return

    rows = []
    for size in SIZES:
        for family in FAMILIES:
            generic = _child("generic", family, size)
            bulk = _child("bulk", family, size)
            assert generic["reuse_bytes"] == bulk["reuse_bytes"]
            assert generic["run_bytes"] == bulk["run_bytes"]
            rows.append({
                "family": family,
                "size": size,
                "generic_peak_rss_kib": generic["ru_maxrss_kib"],
                "bulk_peak_rss_kib": bulk["ru_maxrss_kib"],
                "rss_delta_kib": int(bulk["ru_maxrss_kib"]) - int(generic["ru_maxrss_kib"]),
                "generic_peak_index_entries": generic["peak_index_entries"],
                "bulk_peak_index_entries": bulk["peak_index_entries"],
                "generic_retained_index_payload_bytes": generic["retained_index_payload_bytes"],
                "bulk_retained_index_payload_bytes": bulk["retained_index_payload_bytes"],
                "opportunity_byte_parity": True,
            })

    print(json.dumps({
        "experiment": "ONE-G0.2 bulk digest isolated RSS probe",
        "platform_note": (
            "Linux ru_maxrss is KiB and includes interpreter/input/runtime baseline; "
            "fresh child processes make generic/bulk absolute peaks comparable but the "
            "difference is evidence, not a heap-only allocation measurement."
        ),
        "rows": rows,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
