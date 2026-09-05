"""ONE-G0.2 proof-led branch-and-bound admission transfer.

Frozen before result-bearing execution.

The immutable stratified-proof damage envelope showed a new causal owner: the global >=50% coverage
majority prevents exact proof while 16-32 KiB of real marginal shifted reuse survives. This experiment
removes only that majority prerequisite. It preserves the 64-byte coverage stride, signed shifts
{-2,-1,+1,+2}, inherited four-hit nomination floor, sixteen deterministic proof strata, one supported
proof owner per stratum, four exact 64-byte proofs for admission, sixteen-attempt ceiling, 5% writer-cost
ceiling and 25% modeled read ceiling. Exact proof now owns specificity.

Hypothesis: distributed exact proof makes the global majority redundant. The proof-led gate must preserve
all inherited negative/positive classifications, reject the every-32-byte fragmented false pattern, retain
the every-96-byte positive control, and recover every frozen contiguous-damage row with >=16 KiB positive
marginal minimizer opportunity.

Disproof: any false admission in the inherited matrix, any lost inherited positive, any >=16 KiB damage-
envelope positive still missed, >5% gate/incremental-selector cost, or >25% modeled read traffic retires
proof-led admission. Do not change the support floor, proof count, attempts, shifts, strata or corpora after
result. Failure should trigger a structural opportunity lower bound, not threshold tuning.
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
from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR,
    _cases,
    FIXED_MAX_INDEX_ENTRIES,
    MIN_RUN,
    WINDOW,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_minimizer_miy import _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost
from benchmarks.one.one_g02_shift_coverage_false_pattern_transfer import _fragmented_shift
from experiments.one.observe import observe

MAX_COST_RATIO = 0.05
MAX_READ_FRACTION = 0.25
MIN_DAMAGE_MARGINAL = 16 * 1024
DAMAGE_WIDTHS_KIB = (1, 4, 8, 16, 24, 32, 40, 48, 52, 56, 60)


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
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-bb-proof-led-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_shift_branch_bound_proof_led_kernel.c"),
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            "-o", str(lib),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
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


def _damage_case(seed: int, width: int, placement: str) -> bytes:
    n = 64 * 1024
    a = random.Random(seed).randbytes(n)
    b = bytearray(b"X" + a[:-1])
    if placement == "front":
        lo = 0
    elif placement == "middle":
        lo = (n - width) // 2
    elif placement == "tail":
        lo = n - width
    else:
        raise ValueError(placement)
    lo -= lo % 64
    hi = min(n, lo + width)
    for j in range(lo, hi):
        b[j] ^= (0xA9 + j * 17 + (j - lo) * 29) & 0xFF
    return a + bytes(b)


def _matrix():
    cases: dict[str, tuple[bytes, bool]] = {}
    for name, data in _cases().items():
        cases[name] = (data, False)
    basis = random.Random(4876).randbytes(8192)
    cases["starved_repeat_basis_8k_16k"] = (basis * 2, False)
    cases["starved_shifted_basis_8k_insert1"] = (basis + b"X" + basis, False)
    for name, data in hostile_cases().items():
        cases["hostile_" + name] = (data, False)
    cases["false_fragmented_shift_every32"] = (_fragmented_shift(8101, 65536, 32), False)
    cases["fragmented_shift_every96_control"] = (_fragmented_shift(8102, 65536, 96), False)
    for wi, width_kib in enumerate(DAMAGE_WIDTHS_KIB):
        for pi, placement in enumerate(("front", "middle", "tail")):
            name = f"damage_{placement}_{width_kib}k_plus1"
            cases[name] = (_damage_case(12000 + wi * 7 + pi, width_kib * 1024, placement), True)
    return cases


def run():
    lib, td = _build()
    try:
        fn = lib.one_g02_shift_branch_bound_proof_led
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
        fn.restype = ctypes.c_int
        dispatch, gear_only = _bind_cost(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)

        rows = []
        classification_ok = True
        damage_ok = True
        cost_ok = True
        reads_ok = True
        for name, (data, is_damage) in _matrix().items():
            fixed = observe(data, min_run=MIN_RUN, chunk_size=WINDOW,
                            max_index_entries=FIXED_MAX_INDEX_ENTRIES)
            mini = _minimizer_observe(data)
            marginal = mini.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            positive = marginal > 0
            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            ns, out = _median(fn, arr, len(data))
            enabled = fixed.stats.reuse_opportunity_bytes == 0 and int(out.exact_proofs) >= 4
            correct = enabled == positive
            classification_ok &= correct
            if is_damage and marginal >= MIN_DAMAGE_MARGINAL:
                damage_ok &= enabled

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

            rows.append({
                "case": name,
                "damage_case": is_damage,
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
            })

        passed = classification_ok and damage_ok and cost_ok and reads_ok
        return {
            "schema": "cmpct-one-g02-shift-branch-bound-proof-led-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_min_hits": 4,
            "frozen_exact_proofs": 4,
            "frozen_max_proof_attempts": 16,
            "frozen_strata": 16,
            "frozen_proof_bytes": 64,
            "frozen_max_cost_ratio": MAX_COST_RATIO,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "frozen_damage_marginal_floor": MIN_DAMAGE_MARGINAL,
            "decision": "advance_proof_led_admission" if passed else "retire_proof_led_admission",
            "claim_boundary": "writer-discovery admission research only; no reader/product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_proof_led_admission" else 1)
