"""ONE-G0.2 exclusive non-zero-shift opportunity gate falsifier.

Referee freeze before result-bearing execution
==============================================
The preceding sparse-shift gate retained both known positive-marginal shifted cases but failed for two
causal reasons: it falsely enabled zero-filled shift-invariant data, and its hash-every-candidate probe
cost 8.36% of avoided selector work on the 16 KiB hard-rescue case, above the frozen 5% budget.

This superseding experiment changes the *information signal*, not the old threshold.  A sample contributes
non-zero-shift evidence only when the corresponding zero-shift sample does not already match.  If zero
shift matches, non-zero comparisons are skipped because they cannot add exclusive displacement evidence.
The inherited 4/8 evidence threshold is unchanged.  FNV hashing is replaced by exact 64-byte equality in
eight-byte words with early exit; modeled compared bytes charge both sides of every word actually read.

Frozen hypothesis
-----------------
Exclusive non-zero-shift evidence will preserve every positive-marginal case from the same opportunity
matrix, reject every zero-marginal case, and reduce the probe to <=5% of the promoted selector's
incremental cost on every input >=8 KiB while reading <=25% of each such input.

Disproof
--------
Retire this gate shape if any positive-marginal case is not enabled, any zero-marginal case is enabled,
any >=8 KiB row exceeds 0.05x incremental selector cost, or any >=8 KiB row exceeds 25% modeled read
traffic.  Do not tune the 4/8 threshold, sample positions, shifts, or budgets after result-bearing run.
A pass is still writer-discovery headroom only; the probe must later be fused into existing observation
traffic before any product-speed claim.
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

from benchmarks.one.one_g02_gear_replacement_ab import (
    _GEAR, _cases, FIXED_MAX_INDEX_ENTRIES, MIN_RUN, WINDOW,
)
from benchmarks.one.one_g02_minimizer_gear_ab import _minimizer_observe
from benchmarks.one.one_g02_minimizer_miy import (
    _bind as _bind_cost, _dispatch_call, _gear_call, _paired_cost,
)
from experiments.one.observe import observe

MATCH_THRESHOLD = 4  # inherited unchanged from the failed sparse-shift gate
MAX_COST_RATIO = 0.05
MAX_READ_FRACTION = 0.25


class GateResult(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64),
        ("zero_shift_matches", ctypes.c_uint64),
        ("exclusive_shift_matches", ctypes.c_uint64),
        ("compared_bytes", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64),
    ]


class OldGateResult(ctypes.Structure):
    _fields_ = [
        ("samples", ctypes.c_uint64),
        ("matched_samples", ctypes.c_uint64),
        ("compared_bytes", ctypes.c_uint64),
        ("best_shift", ctypes.c_int64),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-exclusive-shift-gate-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_exclusive_shift_gate_kernel.c"),
            str(here / "one_g02_sparse_shift_gate_kernel.c"),
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_segmented_counter_kernel.c"),
            str(here / "one_g02_minimizer_offset_only_kernel.c"),
            str(here / "one_g02_minimizer_size_dispatch_tail_kernel.c"),
            "-o", str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def _median_probe(fn, result_type, arr, n):
    out = result_type()
    fn(arr, n, ctypes.byref(out))
    vals = []
    for _ in range(51):
        t = time.perf_counter_ns()
        fn(arr, n, ctypes.byref(out))
        vals.append(time.perf_counter_ns() - t)
    return float(statistics.median(vals)), out


def run():
    cases = _cases()
    starved = random.Random(4876).randbytes(8 * 1024)
    cases["starved_repeat_basis_8k_16k"] = starved * 2
    cases["starved_shifted_basis_8k_insert1"] = starved + b"X" + starved

    lib, td = _build()
    try:
        probe = lib.one_g02_exclusive_shift_gate
        probe.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(GateResult)]
        probe.restype = ctypes.c_int
        old_probe = lib.one_g02_sparse_shift_gate
        old_probe.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(OldGateResult)]
        old_probe.restype = ctypes.c_int
        dispatch, gear_only = _bind_cost(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)

        rows = []
        positives = []
        predicted = []
        recall = True
        specificity = True
        cost_ok = True
        reads_ok = True

        for name, data in cases.items():
            fixed = observe(
                data, min_run=MIN_RUN, chunk_size=WINDOW,
                max_index_entries=FIXED_MAX_INDEX_ENTRIES,
            )
            minimizer = _minimizer_observe(data)
            marginal = minimizer.reuse_opportunity_bytes - fixed.stats.reuse_opportunity_bytes
            positive = marginal > 0
            if positive:
                positives.append(name)

            arr = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            pns, pout = _median_probe(probe, GateResult, arr, len(data))
            old_ns, old_out = _median_probe(old_probe, OldGateResult, arr, len(data))
            enable = (
                fixed.stats.reuse_opportunity_bytes == 0
                and int(pout.exclusive_shift_matches) >= MATCH_THRESHOLD
            )
            if enable:
                predicted.append(name)

            recall &= (not positive) or enable
            specificity &= positive or (not enable)
            cost_ratio = None
            read_fraction = None
            if len(data) >= 8192:
                _, _, incremental = _paired_cost(
                    lambda: _gear_call(gear_only, gear, arr, len(data)),
                    lambda: _dispatch_call(dispatch, gear, arr, len(data)),
                )
                cost_ratio = pns / incremental
                read_fraction = int(pout.compared_bytes) / len(data)
                cost_ok &= cost_ratio <= MAX_COST_RATIO
                reads_ok &= read_fraction <= MAX_READ_FRACTION

            rows.append({
                "case": name,
                "input_bytes": len(data),
                "fixed_opportunity_bytes": fixed.stats.reuse_opportunity_bytes,
                "minimizer_opportunity_bytes": minimizer.reuse_opportunity_bytes,
                "marginal_opportunity_bytes": marginal,
                "positive_marginal": positive,
                "probe_samples": int(pout.samples),
                "zero_shift_matches": int(pout.zero_shift_matches),
                "exclusive_shift_matches": int(pout.exclusive_shift_matches),
                "best_shift": int(pout.best_shift),
                "probe_compared_bytes": int(pout.compared_bytes),
                "probe_read_fraction": read_fraction,
                "probe_median_ns": pns,
                "old_sparse_probe_median_ns": old_ns,
                "exclusive_over_old_probe_elapsed_ratio": pns / old_ns if old_ns else None,
                "old_matched_samples": int(old_out.matched_samples),
                "old_best_shift": int(old_out.best_shift),
                "probe_over_incremental_selector": cost_ratio,
                "gate_enable": enable,
            })

        passed = recall and specificity and cost_ok and reads_ok
        return {
            "schema": "cmpct-one-g02-exclusive-shift-gate-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_match_threshold": MATCH_THRESHOLD,
            "frozen_max_cost_ratio": MAX_COST_RATIO,
            "frozen_max_read_fraction": MAX_READ_FRACTION,
            "positive_marginal_cases": positives,
            "gate_enabled_cases": predicted,
            "decision": "advance_exclusive_shift_gate" if passed else "retire_exclusive_shift_gate",
            "claim_boundary": "writer opportunity-gating headroom only; exact sparse reads remain extra observation traffic and are not fused-observer/product/comparator/release authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "advance_exclusive_shift_gate" else 1)
