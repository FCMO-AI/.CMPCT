from __future__ import annotations

"""Fresh-process causal referee for compact-locator parser state.

Mission Lock
============
Use one deterministic, canonical near-ceiling LOC1 byte string for both contenders. The legacy parser
materializes a dict/list/tuple record table; the v4 parser validates the same bytes and retains only the
bounded raw buffer plus scalar counters. Codec/format bytes, locality economics and Office corpus are not
part of this micro-referee.

Hypothesis: on the identical locator, both parsers accept and report the same record cardinality, while
the streaming parser has lower fresh-process peak RSS. Disproof: parse failure/cardinality mismatch or
streaming RSS >= legacy RSS. Timing is reported, not gated; trading all memory for absurd CPU would be
visible rather than silently accepted.
"""

import argparse
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4

SCHEMA = "cmpct-v030-r4-compact-locator-parser-resource-v1"
TARGET_RAW_BYTES = 900_000


def _count_old(loc: dict) -> int:
    return sum(len(rows) for rows in loc.values())


def worker(mode: str, raw_path: Path) -> dict:
    raw = raw_path.read_bytes()
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    if mode == "legacy":
        parsed = V1._parse_locator(raw)
        records = _count_old(parsed)
        retained_shape = "dict-list-tuple-table"
    elif mode == "streaming":
        parsed = V4._parse_locator_streaming(raw)
        records = int(parsed.record_count)
        retained_shape = "raw-buffer-plus-scalars"
    else:
        raise ValueError(mode)
    cpu = time.process_time() - cpu0
    wall = time.perf_counter() - wall0
    # Linux GitHub runners report ru_maxrss in KiB.
    rss_kib = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return {
        "mode": mode,
        "raw_bytes": len(raw),
        "records": records,
        "parse_cpu_s": cpu,
        "parse_wall_s": wall,
        "peak_rss_kib": rss_kib,
        "retained_shape": retained_shape,
    }


def _fresh(mode: str, raw_path: Path) -> dict:
    cp = subprocess.run(
        [sys.executable, __file__, "--worker-mode", mode, "--raw", str(raw_path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(cp.stdout.strip().splitlines()[-1])


def run(work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    raw = V4._large_valid_locator(TARGET_RAW_BYTES)
    # Both implementations see exactly these persisted bytes.
    raw_path = work / "near-ceiling.loc1"
    raw_path.write_bytes(raw)
    legacy = _fresh("legacy", raw_path)
    streaming = _fresh("streaming", raw_path)
    same = legacy["records"] == streaming["records"] and legacy["raw_bytes"] == streaming["raw_bytes"] == len(raw)
    rss_delta = legacy["peak_rss_kib"] - streaming["peak_rss_kib"]
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "input": {"raw_bytes": len(raw), "records": streaming["records"], "deterministic": True},
        "legacy": legacy,
        "streaming": streaming,
        "comparison": {
            "same_input_and_cardinality": same,
            "peak_rss_reduction_kib": rss_delta,
            "peak_rss_ratio_streaming_over_legacy": streaming["peak_rss_kib"] / legacy["peak_rss_kib"],
            "cpu_ratio_streaming_over_legacy": streaming["parse_cpu_s"] / legacy["parse_cpu_s"],
            "wall_ratio_streaming_over_legacy": streaming["parse_wall_s"] / legacy["parse_wall_s"],
        },
        "hypothesis": {"streaming_parser_removes_measured_record_table_rss_debt": same and rss_delta > 0},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_raw_locator_bytes": True,
            "fresh_process_per_contender": True,
            "timing_reported_not_thresholded": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker-mode", choices=["legacy", "streaming"])
    p.add_argument("--raw", type=Path)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-locator-parser-resource-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-locator-parser-resource.json"))
    a = p.parse_args()
    if a.worker_mode:
        if a.raw is None:
            p.error("--raw is required with --worker-mode")
        print(json.dumps(worker(a.worker_mode, a.raw), sort_keys=True))
        return
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps(d, sort_keys=True))


if __name__ == "__main__":
    main()
