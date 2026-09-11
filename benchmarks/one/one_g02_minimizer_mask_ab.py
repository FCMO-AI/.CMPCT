"""ONE-G0.2 preregistered branch-wrap vs power-of-two masked-ring A/B.

Mission lock: the previous exact-head A/B showed that removing runtime modulo owns roughly
15% of compiled rolling-minimum cost but failed its all-large-case promotion gate. This test
asks whether ring addressing itself remains a material owner after branch-wrap. Both arms
implement identical Gear + rightmost-minimum semantics; the candidate only replaces bounded
branch/single-subtract wrap with a power-of-two mask for the already-frozen 4096 span.

Frozen decision rule before result-bearing execution:
* exact semantic tuple equality with Python on every case;
* masked-ring median <= 0.90 * branch-wrap median on every large case to call residual ring
  addressing a material remaining owner;
* masked-ring median <= 1.05 * branch-wrap median on every tested case.
Otherwise retire ring-address arithmetic as the primary remaining cost owner and move causal
work into the monotonic-minimum maintenance itself. No proof, extension, index, Law, wire or
reader cost is gifted.
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

from benchmarks.one.one_g02_minimizer_native_probe import (
    _KernelResult,
    _cases,
    _python_recurrence,
    MINIMIZER_SPAN,
    REPETITIONS,
    WINDOW,
    _GEAR,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES

MATERIAL_SPEED_RATIO = 0.90
MAX_REGRESSION_RATIO = 1.05


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-mask-")
    library = Path(tempdir.name) / "libone_g02_mask_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_branch_kernel.c"),
            str(here / "one_g02_minimizer_mask_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind(lib: ctypes.CDLL, name: str):
    fn = getattr(lib, name)
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    fn.restype = ctypes.c_int
    return fn


def _call(fn, gear, data_array, length: int) -> tuple[int, int, int, int]:
    out = _KernelResult()
    rc = fn(data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"kernel failed: {rc}")
    return int(out.emitted), int(out.peak_queue), int(out.final_state), int(out.positions_considered)


def _median_ns(fn) -> int:
    samples: list[int] = []
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        fn()
        samples.append(time.perf_counter_ns() - start)
    return int(statistics.median(samples))


def run() -> dict[str, object]:
    if MINIMIZER_SPAN <= 0 or MINIMIZER_SPAN & (MINIMIZER_SPAN - 1):
        raise AssertionError("frozen minimizer span must be a power of two for this experiment")
    lib, tempdir = _build()
    try:
        branch = _bind(lib, "one_g02_minimizer_branch_kernel")
        masked = _bind(lib, "one_g02_minimizer_mask_kernel")
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        material_large_ok = True
        no_regression_ok = True
        for name, data in _cases().items():
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected = _python_recurrence(data)
            branch_tuple = _call(branch, gear, data_array, len(data))
            masked_tuple = _call(masked, gear, data_array, len(data))
            equal = branch_tuple == masked_tuple == expected
            semantic_ok &= equal
            if not equal:
                raise AssertionError(
                    f"semantic mismatch {name}: expected={expected} branch={branch_tuple} masked={masked_tuple}"
                )
            branch_ns = _median_ns(lambda: _call(branch, gear, data_array, len(data)))
            masked_ns = _median_ns(lambda: _call(masked, gear, data_array, len(data)))
            ratio = masked_ns / branch_ns
            if name in LARGE_CASES:
                material_large_ok &= ratio <= MATERIAL_SPEED_RATIO
            no_regression_ok &= ratio <= MAX_REGRESSION_RATIO
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "branch_wrap_median_ns": branch_ns,
                "masked_ring_median_ns": masked_ns,
                "masked_over_branch_elapsed_ratio": ratio,
                "masked_speedup_over_branch": branch_ns / masked_ns,
                "semantic_tuple_equal": equal,
            })
        material_owner = semantic_ok and material_large_ok and no_regression_ok
        return {
            "schema": "cmpct-one-g02-minimizer-mask-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "minimizer_span": MINIMIZER_SPAN,
            "hypothesis": "ring-address arithmetic remains a material owner after branch-wrap, and a power-of-two mask removes at least another 10% on every large case without semantic change",
            "disproof": "semantic inequality, less than 10% improvement on any large case, or more than 5% regression on any tested case retires ring addressing as the primary remaining minimizer cost owner",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "decision": "ring_addressing_remains_material_owner" if material_owner else "retire_ring_addressing_as_primary_remaining_owner",
            "claim_boundary": "encoder discovery microkernel A/B only; excludes exact proof, extension, index, Law, wire and reader costs and is not product-speed evidence",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
