"""ONE-G0.2 preregistered modulo-ring vs branch-wrap microkernel A/B.

Mission lock: test one causal ownership hypothesis only. Both C arms implement identical Gear +
rightmost-minimum semantics; the candidate changes ring wrapping from runtime modulo to bounded
branch/single-subtract arithmetic. No proof, index, extension, Law, wire or reader work is gifted.

Promotion rule is frozen before result-bearing execution:
* exact semantic tuple equality with Python on every case;
* branch-wrap median <= 0.85 * modulo median on every large case;
* branch-wrap median <= 1.05 * modulo median on every case.
Otherwise the modulo-ownership hypothesis is rejected or remains insufficient.
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

LARGE_CASES = {
    "random_1mib",
    "zlib_random_1mib",
    "exact_pair_512k",
    "shifted_pair_512k_insert1",
    "repeated_64k_basis_1mib",
}
MATERIAL_SPEED_RATIO = 0.85
MAX_REGRESSION_RATIO = 1.05


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-wrap-")
    library = Path(tempdir.name) / "libone_g02_wrap_ab.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_branch_kernel.c"),
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
    lib, tempdir = _build()
    try:
        modulo = _bind(lib, "one_g02_minimizer_kernel")
        branch = _bind(lib, "one_g02_minimizer_branch_kernel")
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        semantic_ok = True
        material_large_ok = True
        no_regression_ok = True
        for name, data in _cases().items():
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected = _python_recurrence(data)
            modulo_tuple = _call(modulo, gear, data_array, len(data))
            branch_tuple = _call(branch, gear, data_array, len(data))
            equal = modulo_tuple == branch_tuple == expected
            semantic_ok &= equal
            if not equal:
                raise AssertionError(
                    f"semantic mismatch {name}: expected={expected} modulo={modulo_tuple} branch={branch_tuple}"
                )
            modulo_ns = _median_ns(lambda: _call(modulo, gear, data_array, len(data)))
            branch_ns = _median_ns(lambda: _call(branch, gear, data_array, len(data)))
            ratio = branch_ns / modulo_ns
            if name in LARGE_CASES:
                material_large_ok &= ratio <= MATERIAL_SPEED_RATIO
            no_regression_ok &= ratio <= MAX_REGRESSION_RATIO
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "large_case": name in LARGE_CASES,
                "modulo_median_ns": modulo_ns,
                "branch_wrap_median_ns": branch_ns,
                "branch_over_modulo_elapsed_ratio": ratio,
                "branch_speedup_over_modulo": modulo_ns / branch_ns,
                "semantic_tuple_equal": equal,
            })
        promote = semantic_ok and material_large_ok and no_regression_ok
        return {
            "schema": "cmpct-one-g02-minimizer-wrap-ab-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "hypothesis": "runtime modulo is a material causal owner of rolling-minimum cost and bounded branch-wrap removes it without semantic change",
            "disproof": "semantic inequality, less than 15% median improvement on any large case, or more than 5% regression on any tested case rejects promotion",
            "frozen_material_speed_ratio": MATERIAL_SPEED_RATIO,
            "frozen_max_regression_ratio": MAX_REGRESSION_RATIO,
            "decision": "promote_branch_wrap_for_next_integration_test" if promote else "do_not_promote_branch_wrap",
            "claim_boundary": "encoder discovery microkernel A/B only; excludes proof/index/extension/Law/wire/reader costs and is not product-speed evidence",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
