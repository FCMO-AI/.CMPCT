"""ONE-G0.2 paired generic-direct vs compact-half timing discriminator.

Frozen before result-bearing execution.

The arbitrary-relation transfer reproduced classifications/proof signatures but exceeded the frozen
<=1.10x 32/64 KiB cost ceiling. Pointer rebasing recovered substantial cost; a direct-pointer A/B then
showed carrier/offset ABI overhead was real but not dominant, and an adjacent-vs-far A/B falsified physical
stream separation as the dominant residual. One measurement-shape difference remains: the original
transfer compared independently sampled half-layout and relation medians, while the causal A/Bs use paired
ABBA ordering that is much less exposed to runner frequency/thermal drift.

Hypothesis: a material part of the remaining generic-relation loss is independent-timing bias rather than
intrinsic relation work. Hold source/target bytes, proof semantics, compiler flags and physical packed layout
fixed. Time the direct-pointer relation kernel and compact half-layout proof-led kernel in paired ABBA order.
The candidate advances this attribution only if result structs are identical and direct/half <=1.10 on every
frozen 32/64 KiB case. If any row remains >1.10, retire measurement shape as a sufficient explanation and
move to generated-code/loop-shape attribution. The existing 1.10 transfer ceiling is reused unchanged and
may not be relaxed after result.
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

from benchmarks.one.one_g02_shift_branch_bound_relation_transfer import (
    MAX_RELATIVE_COST,
    Result,
    _relation_cases,
)

SIZES = (32 * 1024, 64 * 1024)
REPETITIONS = 151


def _build():
    here = Path(__file__).parent
    td = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-paired-half-ab-")
    lib = Path(td.name) / "lib.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"),
            "-O3",
            "-std=c11",
            "-fPIC",
            "-shared",
            str(here / "one_g02_shift_branch_bound_relation_direct_kernel.c"),
            str(here / "one_g02_shift_branch_bound_proof_led_kernel.c"),
            "-o",
            str(lib),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    cdll = ctypes.CDLL(str(lib))
    direct = cdll.one_g02_shift_branch_bound_relation_direct
    direct.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.POINTER(Result),
    ]
    direct.restype = ctypes.c_int
    half = cdll.one_g02_shift_branch_bound_proof_led
    half.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(Result)]
    half.restype = ctypes.c_int
    return direct, half, td


def _sig(x: Result):
    return tuple(int(getattr(x, name)) for name, _ in Result._fields_)


def _paired(direct, half, packed: bytes, relation_len: int):
    arr = (ctypes.c_uint8 * len(packed)).from_buffer_copy(packed)
    base = ctypes.addressof(arr)
    src = ctypes.cast(base, ctypes.POINTER(ctypes.c_uint8))
    dst = ctypes.cast(base + relation_len, ctypes.POINTER(ctypes.c_uint8))
    do = Result()
    ho = Result()
    if direct(src, dst, relation_len, ctypes.byref(do)) != 0:
        raise RuntimeError("direct relation kernel failed")
    if half(arr, len(packed), ctypes.byref(ho)) != 0:
        raise RuntimeError("half-layout kernel failed")

    direct_samples = []
    half_samples = []
    for _ in range(REPETITIONS):
        t = time.perf_counter_ns()
        half(arr, len(packed), ctypes.byref(ho))
        h1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns()
        direct(src, dst, relation_len, ctypes.byref(do))
        d1 = time.perf_counter_ns() - t
        t = time.perf_counter_ns()
        direct(src, dst, relation_len, ctypes.byref(do))
        d2 = time.perf_counter_ns() - t
        t = time.perf_counter_ns()
        half(arr, len(packed), ctypes.byref(ho))
        h2 = time.perf_counter_ns() - t
        half_samples.append((h1 + h2) * 0.5)
        direct_samples.append((d1 + d2) * 0.5)

    return (
        float(statistics.median(direct_samples)),
        float(statistics.median(half_samples)),
        do,
        ho,
    )


def run():
    direct, half, td = _build()
    rows = []
    try:
        passed = True
        for size in SIZES:
            for case, (source, target, _expected_enable, _expected_shift) in _relation_cases(size).items():
                direct_ns, half_ns, do, ho = _paired(direct, half, source + target, size)
                exact = _sig(do) == _sig(ho)
                ratio = direct_ns / half_ns
                passed &= exact and ratio <= MAX_RELATIVE_COST
                rows.append(
                    {
                        "relation_bytes": size,
                        "case": case,
                        "direct_median_ns": direct_ns,
                        "half_median_ns": half_ns,
                        "direct_over_half": ratio,
                        "result_struct_exact": exact,
                    }
                )
        return {
            "schema": "cmpct-one-g02-shift-relation-paired-half-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "frozen_sizes": list(SIZES),
            "frozen_repetitions": REPETITIONS,
            "frozen_max_relative_cost": MAX_RELATIVE_COST,
            "decision": "paired_timing_closes_transfer_gap" if passed else "measurement_shape_not_sufficient_residual_owner",
            "claim_boundary": "writer-side causal compute attribution only; no representation/product/comparator authority",
            "rows": rows,
        }
    finally:
        td.cleanup()


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["decision"] == "paired_timing_closes_transfer_gap" else 1)
