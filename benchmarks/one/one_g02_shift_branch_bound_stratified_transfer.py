"""ONE-G0.2 stratified exact-proof rehabilitation for branch-bound shift gating.

Frozen before result-bearing execution.

The preceding immutable hostile transfer retired the fixed-front sixteen-proof topology: damaging only
its first sixteen 64-byte cells left 64,512 bytes of minimizer-only reuse, yet produced zero exact proofs.
This experiment preserves the successful gate's stage-1 coverage semantics, signed shifts, majority rule,
four-proof admission threshold, sixteen-attempt ceiling, 5% incremental-selector compute ceiling and 25%
read-traffic ceiling. It changes only proof topology: exact attempts are distributed across sixteen equal
relation strata, with at most one coverage-supported proof owner per stratum.

Hypothesis: stratification removes contiguous proof-phase fragility without weakening false-pattern
rejection or materially increasing writer cost. The new topology must classify the original gate matrix
correctly and recover positive marginal reuse after front, middle and tail contiguous 1 KiB damage.

Disproof: any oracle classification error, any failure to recover the three contiguous-damage positives,
>5% gate/incremental-selector cost on eligible >=8 KiB rows, or >25% modeled read traffic retires this
stratified topology. Do not move strata, increase proof attempts, change proof size, majority, shifts or
thresholds after result. Failure does not retire cheap-coverage -> exact-proof branch-and-bound itself.
"""
from __future__ import annotations

import ctypes
import json
import os
import random
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_exclusive_shift_gate_transfer import _cases as hostile_cases
from benchmarks.one.one_g02_shift_coverage_false_pattern_transfer import _fragmented_shift
from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    FIXED_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost
from experiments.one.observe import observe

MAX_COST_RATIO = 0.05
MAX_READ_FRACTION = 0.25


class Result(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64),
        ("zero_shift_matches", ctypes.c_uint64),
        ("coverage_compared_bytes", ctypes.c_uint64),
        ("best_hits", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64),
        ("proof_attempts", ctypes.c_uint64),
        ("exact_proofs", ctypes.c_uint64),
        ("proof_compared_bytes", ctypes.c_uint64),
        ("strata_with_support", ctypes.c_uint64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-bb-stratified-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O3",
            "-std=c11",
            "-fPIC",
            "-shared",
            str(here / "one_g02_shift_branch_bound_stratified_kernel.c"),
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            "-o",
            str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _median(fn, arr, n):
    out = Result()
    fn(arr, n, ctypes.byref(out))
    vals = []
    for _ in range(51):
        t = time.perf_counter_ns()
        fn(arr, n, ctypes.byref(out))
        vals.append(time.perf_counter_ns() - t)
    return float(statistics.median(vals)), out


def _damaged_shift(seed: int, n: int, region: str) -> bytes:
    a = random.Random(seed).randbytes(n)
    b = bytearray(b"X" + a[:-1])
    width = 16 * 64
    if region == "front":
        lo = 0
    elif region == "middle":
        lo = (n - width) // 2
        lo -= lo % 64
    elif region == "tail":
        lo = n - width
        lo -= lo % 64
    else:
        raise ValueError(region)
    hi = min(n, lo + width)
    for j in range(lo, hi):
        b[j] ^= (0x5D + (j - lo) * 11 + j) & 0xFF
    return a + bytes(b)


def _matrix():
    cases = _cases()
    basis = random.Random(4876).randbytes(8192)
    cases["starved_repeat_basis_8k_16k"] = basis * 2
    cases["starved_shifted_basis_8k_insert1"] = basis + b"X" + basis
    for k, v in hostile_cases().items():
        cases["hostile_" + k] = v
    cases["false_fragmented_shift_every32"] = _fragmented_shift(8101, 65536, 32)
    cases["fragmented_shift_every96_control"] = _fragmented_shift(8102, 65536, 96)
    for i, region in enumerate(("front", "middle", "tail")):
        cases[f"contiguous_damage_{region}_plus1_64k"] = _damaged_shift(9901 + i, 64 * 1024, region)
    return cases


def run():
    lib, td = _build()
    try:
        fn = lib.one_g02_shift_branch_bound_stratified
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
        fn.restype = ctypes.c_int
        dispatch, gear_only = _bind_cost(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        classification_ok = True
        cost_ok = True
        reads_ok = True
        damaged_ok = True
        for name, data in _matrix().items():
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW, max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            mini = _minimizer_observe(data)
            marginal = mini.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            positive = marginal > 0
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            ns, out = _median(fn, arr, len(data))
            enabled = fixed.stats.reuse_opportunity_bytes == 0 and int(out.exact_proofs) >= 4
            correct = enabled == positive
            classification_ok &= correct
            if name.startswith("contiguous_damage_"):
                damaged_ok &= positive and enabled
            ratio = None
            read_fraction = None
            if len(data) >= 8192 and fixed.stats.reuse_opportunity_bytes == 0:
                _, _, inc = _paired_cost(
                    lambda: _gear_call(gear_only, gear, arr, len(data)),
                    lambda: _dispatch_call(dispatch, gear, arr, len(data)),
                )
                ratio = ns / inc
                read_fraction = (int(out.coverage_compared_bytes) + int(out.proof_compared_bytes)) / len(data)
                cost_ok &= ratio <= MAX_COST_RATIO
                reads_ok &= read_fraction <= MAX_READ_FRACTION
            rows.append(
                {
                    "case": name,
                    "input_bytes": len(data),
                    "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                    "minimizer_opportunity_bytes": mini.reuse_opportunity_bytes,
                    "marginal_opportunity_bytes": marginal,
                    "positive_marginal": positive,
                    "best_hits": int(out.best_hits),
                    "best_shift": int(out.best_shift),
                    "strata_with_support": int(out.strata_with_support),
                    "proof_attempts": int(out.proof_attempts),
                    "exact_proofs": int(out.exact_proofs),
                    "coverage_compared_bytes": int(out.coverage_compared_bytes),
                    "proof_compared_bytes": int(out.proof_compared_bytes),
                    "read_fraction": read_fraction,
                    "gate_median_ns": ns,
                    "gate_over_incremental_selector": ratio,
                    "gate_enable": enabled,
                    "classification_correct": correct,
                }
            )
        passed = classification_ok and damaged_ok and cost_ok and reads_ok
        return {
            "schema": "cmpct-one-g02-shift-branch-bound-stratified-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_exact_proofs": 4,
            "frozen_max_proof_attempts": 16,
            "frozen_strata": 16,
            "frozen_proof_bytes": 64,
            "frozen_max_cost_ratio": MAX_COST_RATIO,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "decision": "advance_stratified_proof_topology" if passed else "retire_stratified_proof_topology",
            "claim_boundary": "writer-discovery topology rehabilitation only; no reader/product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_stratified_proof_topology" else 1)
