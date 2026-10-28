from __future__ import annotations

"""Fresh-process RSS/heap attribution for the compact LOC1 reader path.

Mission Lock / Referee
======================
The Office compact-locator representation, encoded bytes, 644 B authenticated groups, primary/tail/footer,
1 MiB raw ceiling, fixed 8x locality law and direct canonical-uvarint rule are frozen. This referee changes
no product or research representation. It asks where the previously observed hosted-process RSS belongs.

The same deterministic near-ceiling valid LOC1 byte string is measured in separate fresh processes after:
(1) importing the exact parser stack only, (2) reading/retaining the raw locator bytes, (3) validating the
locator with the v7 direct-rule streaming parser, and (4) parsing the same bytes into the historical retained
record table. Linux current RSS, process high-water RSS, parse CPU/wall and parse-only Python allocation peak
are recorded. The streaming and table parses must recover the exact same record cardinality.

Hypothesis
----------
The compact reader's persistent parser state is not the source of large hosted-process RSS: on identical
bytes the direct-rule streaming parser must retain constant-shape state, allocate less Python heap during
parse than the historical table parser, and add less current RSS over the raw-buffer stage. The streaming
parse-only Python allocation peak must remain <= 4x the raw locator size; this is a deliberately loose
resource ceiling, not an optimization target.

Disproof
--------
False if cardinality differs, the streaming view grows a retained record table, its parse-only Python peak
exceeds 4x raw bytes, or its current-RSS increment is not lower than the historical table parser. A PASS is
resource attribution only: it grants no Office density/locality/release credit and does not excuse the full
hosted-process RSS budget, which must still be measured end-to-end.
"""

import argparse
import gc
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import tracemalloc

from benchmarks import v030_r4_office_compact_monotone_directory_referee as V1
from benchmarks import v030_r4_office_compact_monotone_directory_v4 as V4
from benchmarks import v030_r4_compact_locator_parser_resource_v2 as FAST

SCHEMA = "cmpct-v030-r4-compact-locator-rss-attribution-v1"
TARGET_RAW_BYTES = 900_000


def _current_rss_kib() -> int:
    # Hosted authority is Linux. VmRSS is current resident state; ru_maxrss below is the process high-water.
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except OSError:
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def _records_in_table(table: dict) -> int:
    return sum(len(rows) for rows in table.values())


def worker(mode: str, raw_path: Path | None) -> dict:
    gc.collect()
    import_rss = _current_rss_kib()
    import_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if mode == "import":
        return {
            "mode": mode,
            "current_rss_kib": import_rss,
            "peak_rss_kib": import_peak,
        }

    if raw_path is None:
        raise ValueError("raw path required")
    raw = raw_path.read_bytes()
    gc.collect()
    read_rss = _current_rss_kib()
    read_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if mode == "read":
        return {
            "mode": mode,
            "raw_bytes": len(raw),
            "current_rss_kib": read_rss,
            "peak_rss_kib": read_peak,
            "rss_delta_vs_import_kib": read_rss - import_rss,
        }

    tracemalloc.start()
    cpu0 = time.process_time()
    wall0 = time.perf_counter()
    if mode == "streaming":
        original = V4._read_canonical_uvarint
        V4._read_canonical_uvarint = FAST._read_canonical_uvarint_fast
        try:
            parsed = V4._parse_locator_streaming(raw)
        finally:
            V4._read_canonical_uvarint = original
        records = int(parsed.record_count)
        retained_table = hasattr(parsed, "__dict__") or isinstance(parsed, dict)
        retained_object_bytes = int(sys.getsizeof(parsed))
    elif mode == "table":
        parsed = V1._parse_locator(raw)
        records = _records_in_table(parsed)
        retained_table = True
        retained_object_bytes = int(sys.getsizeof(parsed))
    else:
        raise ValueError(mode)
    cpu = time.process_time() - cpu0
    wall = time.perf_counter() - wall0
    _cur, py_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc.collect()
    final_rss = _current_rss_kib()
    final_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    # Keep parsed live until after RSS sampling so retained-state cost is charged.
    if parsed is None:  # pragma: no cover - prevents accidental lifetime shortening in future edits.
        raise AssertionError
    return {
        "mode": mode,
        "raw_bytes": len(raw),
        "records": records,
        "parse_cpu_s": cpu,
        "parse_wall_s": wall,
        "parse_python_peak_bytes": int(py_peak),
        "retained_parser_object_bytes_shallow": retained_object_bytes,
        "retained_record_table": retained_table,
        "current_rss_kib": final_rss,
        "peak_rss_kib": final_peak,
        "rss_delta_vs_import_kib": final_rss - import_rss,
        "rss_delta_vs_raw_read_kib": final_rss - read_rss,
        "raw_read_current_rss_kib_in_same_process": read_rss,
        "raw_read_peak_rss_kib_in_same_process": read_peak,
    }


def _fresh(mode: str, raw_path: Path | None) -> dict:
    cmd = [sys.executable, __file__, "--worker-mode", mode]
    if raw_path is not None:
        cmd += ["--raw", str(raw_path)]
    cp = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(cp.stdout.strip().splitlines()[-1])


def run(work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    raw = V4._large_valid_locator(TARGET_RAW_BYTES)
    raw_path = work / "near-ceiling.loc1"
    raw_path.write_bytes(raw)

    imp = _fresh("import", None)
    read = _fresh("read", raw_path)
    streaming = _fresh("streaming", raw_path)
    table = _fresh("table", raw_path)

    same = streaming["records"] == table["records"] and streaming["raw_bytes"] == table["raw_bytes"] == len(raw)
    constant_shape = not streaming["retained_record_table"] and streaming["retained_parser_object_bytes_shallow"] < 1024
    heap_ceiling = 4 * len(raw)
    heap_bounded = streaming["parse_python_peak_bytes"] <= heap_ceiling
    heap_better = streaming["parse_python_peak_bytes"] < table["parse_python_peak_bytes"]
    rss_better = streaming["rss_delta_vs_raw_read_kib"] < table["rss_delta_vs_raw_read_kib"]
    supported = same and constant_shape and heap_bounded and heap_better and rss_better

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "input": {
            "raw_locator_bytes": len(raw),
            "streaming_record_count": streaming["records"],
            "table_record_count": table["records"],
        },
        "fresh_process_stages": {
            "import_only": imp,
            "raw_read": read,
            "streaming_direct_rule": streaming,
            "historical_table": table,
        },
        "attribution": {
            "same_input_and_cardinality": same,
            "streaming_constant_shape": constant_shape,
            "streaming_parse_python_peak_ceiling_bytes": heap_ceiling,
            "streaming_parse_python_peak_within_ceiling": heap_bounded,
            "streaming_python_peak_saved_vs_table_bytes": table["parse_python_peak_bytes"] - streaming["parse_python_peak_bytes"],
            "streaming_current_rss_delta_vs_raw_read_kib": streaming["rss_delta_vs_raw_read_kib"],
            "table_current_rss_delta_vs_raw_read_kib": table["rss_delta_vs_raw_read_kib"],
            "streaming_uses_less_incremental_rss_than_table": rss_better,
            "streaming_uses_less_parse_heap_than_table": heap_better,
        },
        "hypothesis": {
            "large_hosted_rss_is_not_persistent_locator_parser_state": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "representation_unchanged": True,
            "fresh_process_per_stage": True,
            "same_deterministic_locator_bytes": True,
            "direct_uvarint_rule": True,
            "no_product_threshold_or_locality_change": True,
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker-mode", choices=["import", "read", "streaming", "table"])
    p.add_argument("--raw", type=Path)
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-locator-rss-attribution-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-locator-rss-attribution.json"))
    a = p.parse_args()
    if a.worker_mode:
        print(json.dumps(worker(a.worker_mode, a.raw), sort_keys=True))
        return
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps(d, sort_keys=True))


if __name__ == "__main__":
    main()
