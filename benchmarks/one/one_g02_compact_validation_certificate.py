"""ONE-G0.2 compact reusable validation-certificate falsifier.

Frozen by ONE_G02_COMPACT_VALIDATION_CERTIFICATE_PREREG_2026-09-09.md.
"""
from __future__ import annotations

import gc
import json
import statistics
import time

from benchmarks.one.one_g02_native_law_terminal_reader import _case
from benchmarks.one.one_g02_selective_preflight_scaling import _with_unrelated_nodes
from experiments.one.range_vm import RangeEvaluator
from experiments.one.validated_program import (
    validate_program_snapshot,
    validate_program_snapshot_compact,
)

ROOT_BYTES = 128 * 1024
REQUEST_START = 0
REQUEST_BYTES = 4096
UNRELATED_COUNTS = (0, 64, 256, 1024, 4096)
ROUNDS = 15
MAX_MEMORY_RATIO_AT_4096 = 0.40
MAX_BYTES_PER_ENTRY = 12
MAX_BYTES_FIXED = 256
MAX_MEDIAN_REQUEST_CPU_RATIO = 1.15
MAX_WORST_REQUEST_CPU_RATIO = 1.30
MAX_MEDIAN_OPEN_CPU_RATIO = 1.25


def _median_cpu_ns(fn, rounds=ROUNDS):
    value = fn()
    samples = []
    enabled = gc.isenabled()
    try:
        if enabled:
            gc.disable()
        for _ in range(rounds):
            c0 = time.process_time_ns()
            value = fn()
            samples.append(time.process_time_ns() - c0)
    finally:
        if enabled:
            gc.enable()
    return value, int(statistics.median(samples))


def run():
    rows = []
    request_ratios = []
    open_ratios = []
    semantic_ok = True

    for family in ("add8", "xor"):
        base = _case(ROOT_BYTES, family)
        for unrelated in UNRELATED_COUNTS:
            program = _with_unrelated_nodes(base, unrelated)
            ordinary, ordinary_open_cpu = _median_cpu_ns(
                lambda p=program: validate_program_snapshot(p)
            )
            compact, compact_open_cpu = _median_cpu_ns(
                lambda p=program: validate_program_snapshot_compact(p)
            )

            if compact.preflight_entry_count != ordinary.preflight_entry_count:
                raise AssertionError("compact certificate entry count diverged")
            if tuple(compact.preflight.lengths) != tuple(ordinary.preflight.lengths):
                raise AssertionError("compact certificate node lengths diverged")
            if compact.preflight.max_depth != ordinary.preflight.max_depth:
                raise AssertionError("compact certificate max depth diverged")
            if compact.preflight.worst_work_bytes != ordinary.preflight.worst_work_bytes:
                raise AssertionError("compact certificate work bound diverged")

            ordinary_reader = RangeEvaluator.from_validated(ordinary)
            compact_reader = RangeEvaluator.from_validated(compact)
            ordinary_result, ordinary_request_cpu = _median_cpu_ns(
                lambda r=ordinary_reader: r.reconstruct(
                    "current", REQUEST_START, REQUEST_BYTES
                )
            )
            compact_result, compact_request_cpu = _median_cpu_ns(
                lambda r=compact_reader: r.reconstruct(
                    "current", REQUEST_START, REQUEST_BYTES
                )
            )
            exact = compact_result == ordinary_result
            semantic_ok &= exact
            if not exact:
                raise AssertionError("compact certificate range result diverged")

            retained_ratio = compact.python_preflight_bytes / max(
                ordinary.python_preflight_bytes, 1
            )
            request_ratio = compact_request_cpu / max(ordinary_request_cpu, 1)
            open_ratio = compact_open_cpu / max(ordinary_open_cpu, 1)
            request_ratios.append(request_ratio)
            open_ratios.append(open_ratio)
            rows.append(
                {
                    "family": family,
                    "root_bytes": ROOT_BYTES,
                    "request_bytes": REQUEST_BYTES,
                    "unrelated_nodes": unrelated,
                    "program_nodes": len(program.nodes),
                    "ordinary_open_cpu_ns": ordinary_open_cpu,
                    "compact_open_cpu_ns": compact_open_cpu,
                    "compact_over_ordinary_open_cpu": open_ratio,
                    "ordinary_request_cpu_ns": ordinary_request_cpu,
                    "compact_request_cpu_ns": compact_request_cpu,
                    "compact_over_ordinary_request_cpu": request_ratio,
                    "ordinary_python_preflight_bytes": ordinary.python_preflight_bytes,
                    "compact_python_preflight_bytes": compact.python_preflight_bytes,
                    "compact_over_ordinary_python_preflight": retained_ratio,
                    "modeled_preflight_bytes": compact.modeled_preflight_bytes,
                    "preflight_entries": compact.preflight_entry_count,
                    "compact_bytes_per_entry_plus_scalars": (
                        compact.python_preflight_bytes
                        / max(compact.preflight_entry_count, 1)
                    ),
                    "semantic_ok": exact,
                }
            )

    large_rows = [r for r in rows if r["unrelated_nodes"] == 4096]
    memory_large_ok = all(
        r["compact_over_ordinary_python_preflight"] <= MAX_MEMORY_RATIO_AT_4096
        for r in large_rows
    )
    compact_size_ok = all(
        r["compact_python_preflight_bytes"]
        <= MAX_BYTES_PER_ENTRY * r["preflight_entries"] + MAX_BYTES_FIXED
        for r in rows
    )
    median_request_ratio = statistics.median(request_ratios)
    worst_request_ratio = max(request_ratios)
    median_open_ratio = statistics.median(open_ratios)
    gates = {
        "semantic_ok": semantic_ok,
        "large_retained_memory_ok": memory_large_ok,
        "compact_absolute_size_ok": compact_size_ok,
        "median_request_cpu_ok": median_request_ratio <= MAX_MEDIAN_REQUEST_CPU_RATIO,
        "worst_request_cpu_ok": worst_request_ratio <= MAX_WORST_REQUEST_CPU_RATIO,
        "median_open_cpu_ok": median_open_ratio <= MAX_MEDIAN_OPEN_CPU_RATIO,
    }
    advance = all(gates.values())
    return {
        "schema": "cmpct-one-g02-compact-validation-certificate-v1",
        "experimental_version": "ONE-G0.2",
        "root_bytes": ROOT_BYTES,
        "request_bytes": REQUEST_BYTES,
        "rounds": ROUNDS,
        "summary": {
            "median_compact_over_ordinary_request_cpu": median_request_ratio,
            "worst_compact_over_ordinary_request_cpu": worst_request_ratio,
            "median_compact_over_ordinary_open_cpu": median_open_ratio,
            "large_retained_memory_ratios": {
                r["family"]: r["compact_over_ordinary_python_preflight"]
                for r in large_rows
            },
            "max_compact_python_preflight_bytes": max(
                r["compact_python_preflight_bytes"] for r in rows
            ),
            "gates": gates,
            "advance": advance,
            "decision": (
                "ADVANCE_COMPACT_VALIDATION_CERTIFICATE"
                if advance
                else (
                    "INVALIDATE_COMPACT_VALIDATION_CERTIFICATE"
                    if not semantic_ok
                    else "HOLD_COMPACT_VALIDATION_CERTIFICATE"
                )
            ),
        },
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, sort_keys=True))
    if not result["summary"]["advance"]:
        raise SystemExit(1)