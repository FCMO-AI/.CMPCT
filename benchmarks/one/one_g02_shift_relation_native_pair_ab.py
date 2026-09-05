"""ONE-G0.2 native-internal generic-relation timing attribution.

Frozen before result-bearing execution.

The paired Python/ctypes ABBA discriminator brought the generic direct-pointer relation kernel inside the
existing <=1.10x transfer ceiling on every frozen 32/64 KiB row, but left a 5.5-9.6% residual versus the
compact half-layout kernel. Because those kernels are only a few microseconds long and the Python call
signatures differ, this experiment removes Python/ctypes from the timed inner loop before any code-shape
optimization is attempted.

The unchanged two C kernels are called in ABBA batches by one C harness. The same run also repeats the
single-call Python ABBA measurement, on the same packed bytes, to estimate how much of the excess disappears
when FFI/timer overhead is amortized.

Hypothesis: Python/ctypes call shape plus per-call timing is the dominant owner of the surviving residual.
It advances only if all result structs are exact, every native direct/half ratio is <=1.05, and for every row
native excess over parity is <=50% of the same-run Python-paired excess (a negative native excess counts as
zero). Failure retires FFI/timing overhead as the dominant residual owner and moves attribution to generated
C code / loop shape. Thresholds are frozen before native result and may not be relaxed after result.
"""
from __future__ import annotations

import ctypes
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import Result, _relation_cases

SIZES = (32 * 1024, 64 * 1024)
PY_REPETITIONS = 101
NATIVE_ROUNDS = 101
BATCH_CALLS = 64
MAX_NATIVE_RATIO = 1.05
MAX_EXCESS_FRACTION = 0.50


class NativeMeasurement(ctypes.Structure):
    _fields_ = [
        ("half_ns_per_call", ctypes.c_double),
        ("direct_ns_per_call", ctypes.c_double),
        ("half_result", Result),
        ("direct_result", Result),
    ]


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-native-pair-ab-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
            str(here / "one_g02_shift_branch_bound_proof_led_kernel.c"),
            str(here / "one_g02_shift_relation_native_pair_kernel.c"),
            "-o", str(lib),
        ],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    direct = cdll.one_g02_shift_branch_bound_relation_direct
    direct.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8),
                       ctypes.c_size_t, ctypes.POINTER(Result)]
    direct.restype = ctypes.c_int
    half = cdll.one_g02_shift_branch_bound_proof_led
    half.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
    half.restype = ctypes.c_int
    native = cdll.one_g02_shift_relation_native_pair_measure
    native.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_size_t,
                       ctypes.POINTER(NativeMeasurement)]
    native.restype = ctypes.c_int
    return direct, half, native, td


def _sig(x: Result):
    return tuple(int(getattr(x, name)) for name, _ in Result._fields_)


def _python_pair(direct, half, arr, relation_len):
    base = ctypes.addressof(arr)
    src = ctypes.cast(base, ctypes.POINTER(ctypes.c_uint8))
    dst = ctypes.cast(base + relation_len, ctypes.POINTER(ctypes.c_uint8))
    do = Result(); ho = Result()
    dvals = []; hvals = []
    for _ in range(PY_REPETITIONS):
        t = time.perf_counter_ns(); half(arr, relation_len * 2, ctypes.byref(ho)); h1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); direct(src, dst, relation_len, ctypes.byref(do)); d1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); direct(src, dst, relation_len, ctypes.byref(do)); d2 = time.perf_counter_ns() - t
        t = time.perf_counter_ns(); half(arr, relation_len * 2, ctypes.byref(ho)); h2 = time.perf_counter_ns() - t
        dvals.append((d1 + d2) * 0.5); hvals.append((h1 + h2) * 0.5)
    return float(statistics.median(dvals)), float(statistics.median(hvals)), do, ho


def _native_pair(native, arr, relation_len):
    dvals = []; hvals = []; last = NativeMeasurement()
    for _ in range(NATIVE_ROUNDS):
        m = NativeMeasurement()
        rc = native(arr, relation_len, BATCH_CALLS, ctypes.byref(m))
        if rc != 0:
            raise RuntimeError(f"native harness failed: {rc}")
        dvals.append(float(m.direct_ns_per_call)); hvals.append(float(m.half_ns_per_call)); last = m
    return float(statistics.median(dvals)), float(statistics.median(hvals)), last.direct_result, last.half_result


def run():
    direct, half, native, td = _build()
    rows = []
    try:
        passed = True
        for size in SIZES:
            for case, (source, target, _expected_enable, _expected_shift) in _relation_cases(size).items():
                packed = source + target
                arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
                pd, ph, pdo, pho = _python_pair(direct, half, arr, size)
                nd, nh, ndo, nho = _native_pair(native, arr, size)
                python_ratio = pd / ph
                native_ratio = nd / nh
                python_excess = max(0.0, python_ratio - 1.0)
                native_excess = max(0.0, native_ratio - 1.0)
                excess_fraction = native_excess / python_excess if python_excess > 0 else (0.0 if native_excess == 0 else float("inf"))
                exact = _sig(pdo) == _sig(pho) == _sig(ndo) == _sig(nho)
                row_ok = exact and native_ratio <= MAX_NATIVE_RATIO and excess_fraction <= MAX_EXCESS_FRACTION
                passed &= row_ok
                rows.append({
                    "relation_bytes": size,
                    "case": case,
                    "python_direct_ns": pd,
                    "python_half_ns": ph,
                    "python_direct_over_half": python_ratio,
                    "native_direct_ns": nd,
                    "native_half_ns": nh,
                    "native_direct_over_half": native_ratio,
                    "native_excess_fraction_of_python_excess": excess_fraction,
                    "result_struct_exact": exact,
                    "row_pass": row_ok,
                })
        return {
            "schema": "cmpct-one-g02-shift-relation-native-pair-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_python_repetitions": PY_REPETITIONS,
            "frozen_native_rounds": NATIVE_ROUNDS,
            "frozen_batch_calls": BATCH_CALLS,
            "frozen_max_native_ratio": MAX_NATIVE_RATIO,
            "frozen_max_excess_fraction": MAX_EXCESS_FRACTION,
            "decision": "ffi_timing_is_dominant_residual_owner" if passed else "ffi_timing_not_dominant_residual_owner",
            "claim_boundary": "writer-side causal compute attribution only; no representation/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run(); print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "ffi_timing_is_dominant_residual_owner" else 1)
