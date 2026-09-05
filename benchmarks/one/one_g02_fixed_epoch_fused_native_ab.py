"""ONE-G0.2 native one-pass fixed+epoch signal fusion A/B.

Referee freeze before result-bearing execution
==============================================
The complete-reference integration gate showed that epoch-min's advantage survives index
and exact-proof bookkeeping, but both reference arms still scan the source twice: once for
the already-required aligned fixed observer and once for the augmentation. ONE explicitly
prefers a fused observation pass. This R2/D2 experiment asks whether combining the fixed
FNV/run signal and scalar starvation-epoch Gear signal into one native byte loop removes a
material amount of execution/memory traffic without changing either signal.

Baseline is the sum of two native calls over the same bytes: fixed-signal kernel + exact
standalone epoch-min kernel. Candidate is one native call producing both traces. Trace
buffers are preallocated identically outside timing. No index/proof work is included here;
that remains the next integration boundary.

Frozen gate:
- fixed hash/start trace exactly equals an independent Python fixed-signal oracle;
- fused fixed trace equals standalone fixed trace exactly;
- fused epoch trace/final state/accounting equals standalone epoch kernel exactly;
- one source scan in fused versus two in baseline by construction;
- on every >=64 KiB row, median fused/baseline elapsed <=0.95x;
- on the hard ~8 KiB rescue row, fused/baseline <=1.05x;
- any exactness failure rejects fusion regardless of speed.

A speed failure is useful negative evidence: it means source-loop/memory-traffic fusion is
not a sufficient owner and the next effort should focus on index/hash/proof architecture.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW, MIN_RUN
from benchmarks.one.one_g02_minimizer_native_probe import MINIMIZER_SPAN
from benchmarks.one.one_g02_starvation_byte_history_native_ab import _cases
from benchmarks.one.one_g02_starvation_epoch_min_native_ab import _E, _bind_epoch, _call_epoch

ROUNDS = 21
FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x100000001B3
U64 = (1 << 64) - 1


class _F(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("bytes_scanned", ctypes.c_uint64),
        ("reserved_state_bytes", ctypes.c_uint64),
    ]


def _bind_fixed(lib):
    fn = lib.one_g02_fixed_signal_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
        ctypes.POINTER(_F), ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _bind_fused(lib):
    fn = lib.one_g02_fixed_epoch_fused_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_F), ctypes.POINTER(_E),
        ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    fn.restype = ctypes.c_int
    return fn


def _fixed_call(fn, arr, n, hashes, starts, cap):
    out = _F()
    rc = fn(arr, n, WINDOW, ctypes.byref(out), hashes, starts, cap)
    if rc:
        raise RuntimeError(f"fixed kernel rc={rc}")
    return out


def _fused_call(fn, gear, arr, n, hashes, starts, fixed_cap, epoch_trace, epoch_cap):
    fo = _F()
    eo = _E()
    rc = fn(
        arr, n, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(fo), ctypes.byref(eo),
        hashes, starts, fixed_cap, epoch_trace, epoch_cap,
    )
    if rc:
        raise RuntimeError(f"fused kernel rc={rc}")
    return fo, eo


def _fixed_oracle(data: bytes):
    hashes = []
    starts = []
    h = FNV_OFFSET
    run_value = data[0] if data else 0
    run_length = 0
    for position, value in enumerate(data):
        if not run_length:
            run_value = value
            run_length = 1
        elif value == run_value:
            run_length += 1
        else:
            run_value = value
            run_length = 1
        h ^= value
        h = (h * FNV_PRIME) & U64
        if (position + 1) % WINDOW == 0:
            fingerprint = h
            h = FNV_OFFSET
            if run_length < max(MIN_RUN, WINDOW):
                hashes.append(fingerprint)
                starts.append(position + 1 - WINDOW)
    return hashes, starts


def _paired(base_fn, fused_fn):
    base_fn(); fused_fn()
    ratios = []
    base_ns = []
    fused_ns = []
    for i in range(ROUNDS):
        if i & 1:
            t0 = time.perf_counter_ns(); fused_fn(); f = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); base_fn(); b = time.perf_counter_ns() - t0
        else:
            t0 = time.perf_counter_ns(); base_fn(); b = time.perf_counter_ns() - t0
            t0 = time.perf_counter_ns(); fused_fn(); f = time.perf_counter_ns() - t0
        base_ns.append(b); fused_ns.append(f); ratios.append(f / b)
    return statistics.median(base_ns), statistics.median(fused_ns), statistics.median(ratios)


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-fixed-epoch-fused-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
         str(here / "one_g02_fixed_epoch_fused_kernel.c"),
         str(here / "one_g02_starvation_epoch_min_kernel.c"), "-o", str(lib)],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(lib)), td


def run():
    lib, td = _build()
    try:
        fixed_fn = _bind_fixed(lib)
        epoch_fn = _bind_epoch(lib)
        fused_fn = _bind_fused(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows = []
        failures = []
        for name, data in _cases().items():
            n = len(data)
            arr = (ctypes.c_uint8 * n).from_buffer_copy(data)
            fixed_cap = max(1, n // WINDOW + 2)
            epoch_cap = max(1, n)
            bh = (ctypes.c_uint64 * fixed_cap)(); bs = (ctypes.c_uint64 * fixed_cap)()
            fh = (ctypes.c_uint64 * fixed_cap)(); fs = (ctypes.c_uint64 * fixed_cap)()
            be = (ctypes.c_uint64 * epoch_cap)(); fe = (ctypes.c_uint64 * epoch_cap)()

            standalone_fixed = _fixed_call(fixed_fn, arr, n, bh, bs, fixed_cap)
            standalone_epoch = _call_epoch(epoch_fn, gear, arr, n, be, epoch_cap)
            fused_fixed, fused_epoch = _fused_call(
                fused_fn, gear, arr, n, fh, fs, fixed_cap, fe, epoch_cap
            )
            oracle_h, oracle_s = _fixed_oracle(data)
            fixed_count = int(standalone_fixed.emitted)
            fused_fixed_count = int(fused_fixed.emitted)
            epoch_count = int(standalone_epoch.emitted)
            fused_epoch_count = int(fused_epoch.emitted)
            standalone_fixed_trace = ([int(bh[i]) for i in range(fixed_count)], [int(bs[i]) for i in range(fixed_count)])
            fused_fixed_trace = ([int(fh[i]) for i in range(fused_fixed_count)], [int(fs[i]) for i in range(fused_fixed_count)])
            standalone_epoch_trace = [int(be[i]) for i in range(epoch_count)]
            fused_epoch_trace = [int(fe[i]) for i in range(fused_epoch_count)]

            exact_fixed = standalone_fixed_trace == (oracle_h, oracle_s) == fused_fixed_trace
            exact_epoch = (
                standalone_epoch_trace == fused_epoch_trace
                and int(standalone_epoch.final_state) == int(fused_epoch.final_state)
                and int(standalone_epoch.positions_considered) == int(fused_epoch.positions_considered)
                and int(standalone_epoch.sparse_anchors) == int(fused_epoch.sparse_anchors)
                and int(standalone_epoch.pulses) == int(fused_epoch.pulses)
            )
            if not exact_fixed or not exact_epoch:
                failures.append({"case": name, "reasons": ["signal_exactness"]})

            def baseline():
                _fixed_call(fixed_fn, arr, n, bh, bs, fixed_cap)
                _call_epoch(epoch_fn, gear, arr, n, be, epoch_cap)

            def fused():
                _fused_call(fused_fn, gear, arr, n, fh, fs, fixed_cap, fe, epoch_cap)

            base_median, fused_median, ratio = _paired(baseline, fused)
            reasons = []
            if n >= 65_536 and ratio > 0.95:
                reasons.append("large_elapsed")
            if name == "transfer_starved_seed10_insert1" and ratio > 1.05:
                reasons.append("hard_elapsed")
            if reasons:
                failures.append({"case": name, "reasons": reasons})
            rows.append({
                "case": name,
                "input_bytes": n,
                "exact_fixed_signal": exact_fixed,
                "exact_epoch_signal": exact_epoch,
                "standalone_source_scans": 2,
                "fused_source_scans": 1,
                "standalone_median_ns": base_median,
                "fused_median_ns": fused_median,
                "fused_over_standalone_elapsed_ratio": ratio,
                "fixed_emitted": fixed_count,
                "epoch_emitted": epoch_count,
                "fixed_state_bytes": int(standalone_fixed.reserved_state_bytes),
                "epoch_state_bytes": int(standalone_epoch.reserved_state_bytes),
            })

        decision = (
            "advance_one_pass_signal_fusion_to_index_integration"
            if not failures
            else "block_one_pass_signal_fusion_on_exactness_or_elapsed"
        )
        return {
            "schema": "cmpct-one-g02-fixed-epoch-fused-native-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "rounds": ROUNDS,
            "gate_failures": failures,
            "decision": decision,
            "claim_boundary": (
                "native encoder signal/pass-fusion evidence only; index/proof integration still owed; "
                "no stored-byte/product/comparator/release authority"
            ),
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
