"""ONE-G0.2 shift-coverage gate falsifier.

Frozen before result-bearing execution.

The deterministic eight-point exclusive gate was cheap but phase-blind. This successor changes the
observation topology: one byte is checked every 64 source bytes across the candidate half-to-half
relation. Zero-shift equality still suppresses non-zero evidence at that point. The inherited four-hit
floor is retained; admission additionally requires majority support for one signed displacement.

The majority rule is fixed before execution to separate a coherent global relation from accidental
1/256 byte matches while tolerating local corruption. Worst-case modeled reads are 10 bytes per 128
input bytes (7.8125%).

Disproof: retire if any positive-marginal case in the combined original+hostile matrix is missed, any
zero-marginal case is enabled, any fixed-opportunity-zero input >=8 KiB exceeds 0.05x the promoted
selector increment, or modeled reads exceed 8% of input. Do not tune stride, majority, shifts, or cost
budgets after result-bearing execution.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_exclusive_shift_gate_transfer import _cases as hostile_cases
from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, _cases, FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost
from experiments.one.observe import observe

MIN_HITS = 4
MAJORITY_NUM = 1
MAJORITY_DEN = 2
MAX_COST_RATIO = 0.05
MAX_READ_FRACTION = 0.08


class CoverageResult(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64),
        ("zero_shift_matches", ctypes.c_uint64),
        ("compared_bytes", ctypes.c_uint64),
        ("exclusive_hits", ctypes.c_uint64 * 4),
        ("best_hits", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-shift-coverage-")
    lib = Path(td.name) / "lib.so"
    subprocess.run([
        os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
        str(here / "one_g02_shift_coverage_gate_kernel.c"),
        str(here / "one_g02_minimizer_kernel.c"),
        str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
        str(here / "one_g02_minimizer_offset_only_kernel.c"),
        str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
        "-o", str(lib),
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ctypes.CDLL(str(lib)), td


def _median_probe(fn, arr, n):
    out = CoverageResult()
    fn(arr, n, ctypes.byref(out))
    values = []
    for _ in range(51):
        t0 = time.perf_counter_ns()
        fn(arr, n, ctypes.byref(out))
        values.append(time.perf_counter_ns() - t0)
    return float(statistics.median(values)), out


def run():
    cases = _cases()
    basis = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = basis * 2
    cases["starved_shifted_basis_8k_insert1"] = basis + b"X" + basis
    for name, data in hostile_cases().items():
        cases[f"hostile_{name}"] = data

    lib, td = _build()
    try:
        probe = lib.one_g02_shift_coverage_gate
        probe.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(CoverageResult)]
        probe.restype = ctypes.c_int
        dispatch, gear_only = _bind_cost(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)

        rows = []
        classification_ok = True
        cost_ok = True
        reads_ok = True
        for name, data in cases.items():
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW,
                            max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            minimizer = _minimizer_observe(data)
            marginal = minimizer.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            positive = marginal > 0
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            pns, out = _median_probe(probe, arr, len(data))
            required_hits = max(MIN_HITS, (int(out.samples) * MAJORITY_NUM + MAJORITY_DEN - 1) // MAJORITY_DEN)
            enabled = fixed.stats.reuse_opportunity_bytes == 0 and int(out.best_hits) >= required_hits
            classification_ok &= enabled == positive

            cost_ratio = None
            read_fraction = None
            if len(data) >= 8192 and fixed.stats.reuse_opportunity_bytes == 0:
                _, _, incremental = _paired_cost(
                    lambda: _gear_call(gear_only, gear, arr, len(data)),
                    lambda: _dispatch_call(dispatch, gear, arr, len(data)),
                )
                cost_ratio = pns / incremental
                read_fraction = int(out.compared_bytes) / len(data)
                cost_ok &= cost_ratio <= MAX_COST_RATIO
                reads_ok &= read_fraction <= MAX_READ_FRACTION

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "minimizer_opportunity_bytes": minimizer.reuse_opportunity_bytes,
                "marginal_opportunity_bytes": marginal,
                "positive_marginal": positive,
                "samples": int(out.samples),
                "zero_shift_matches": int(out.zero_shift_matches),
                "best_hits": int(out.best_hits),
                "required_hits": required_hits,
                "best_shift": int(out.best_shift),
                "compared_bytes": int(out.compared_bytes),
                "read_fraction": read_fraction,
                "probe_median_ns": pns,
                "probe_over_incremental_selector": cost_ratio,
                "gate_enable": enabled,
                "classification_correct": enabled == positive,
            })

        passed = classification_ok and cost_ok and reads_ok
        return {
            "schema": "cmpct-one-g02-shift-coverage-gate-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_stride_bytes": 64,
            "frozen_min_hits": MIN_HITS,
            "frozen_majority": "1/2",
            "frozen_max_cost_ratio": MAX_COST_RATIO,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "decision": "advance_shift_coverage_gate" if passed else "retire_shift_coverage_gate",
            "claim_boundary": "writer opportunity-gating headroom only; extra reads are charged and not yet fused/product authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_shift_coverage_gate" else 1)
