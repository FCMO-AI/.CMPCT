"""ONE-G0.2 diagnostic: same-run residual cost of segmented minima versus Gear-only floor.

This is not a promotion gate. It quantifies how much compute debt remains after the segmented
maintenance Builder, on the same hosted runner and exact source. Product-speed claims remain
forbidden because proof, Law selection, extension and emission are excluded.
"""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR
from benchmarks.one.one_g02_minimizer_block_ab import _median_ns, _python_anchor_trace
from benchmarks.one.one_g02_minimizer_native_probe import _KernelResult, _cases, MINIMIZER_SPAN, WINDOW
from benchmarks.one.one_g02_minimizer_segmented_ab import (
    _SegmentedResult,
    _bind_segmented,
    _call_segmented,
)
from benchmarks.one.one_g02_minimizer_wrap_ab import LARGE_CASES


def _build() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    here = Path(__file__).parent
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-segmented-residual-")
    library = Path(tempdir.name) / "libone_g02_segmented_residual.so"
    subprocess.run(
        [
            os.environ.get("CC", "cc"), "-O3", "-std=c11", "-fPIC", "-shared",
            str(here / "one_g02_minimizer_kernel.c"),
            str(here / "one_g02_minimizer_segmented_kernel.c"),
            "-o", str(library),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return ctypes.CDLL(str(library)), tempdir


def _bind_gear(lib: ctypes.CDLL):
    fn = lib.one_g02_gear_only_kernel
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    fn.restype = ctypes.c_int
    return fn


def _call_gear(fn, gear, data_array, length: int) -> _KernelResult:
    out = _KernelResult()
    rc = fn(data_array, length, gear, WINDOW, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"Gear-only kernel failed: {rc}")
    return out


def run() -> dict[str, object]:
    lib, tempdir = _build()
    try:
        gear_fn = _bind_gear(lib)
        segmented = _bind_segmented(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        for name, data in _cases().items():
            if name not in LARGE_CASES:
                continue
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            expected_trace, expected_state, expected_considered = _python_anchor_trace(data)
            gear_once = _call_gear(gear_fn, gear, data_array, len(data))
            segmented_once = _call_segmented(segmented, gear, data_array, len(data))
            if (
                int(gear_once.final_state) != expected_state
                or int(gear_once.positions_considered) != expected_considered
                or int(segmented_once.final_state) != expected_state
                or int(segmented_once.positions_considered) != expected_considered
                or int(segmented_once.emitted) != len(expected_trace)
            ):
                raise AssertionError(f"semantic/count mismatch for {name}")
            gear_ns = _median_ns(lambda: _call_gear(gear_fn, gear, data_array, len(data)))
            segmented_ns = _median_ns(lambda: _call_segmented(segmented, gear, data_array, len(data)))
            input_mib = len(data) / (1024 * 1024)
            rows.append({
                "case": name,
                "input_bytes": len(data),
                "gear_only_median_ns": gear_ns,
                "segmented_median_ns": segmented_ns,
                "segmented_over_gear_elapsed_ratio": segmented_ns / gear_ns,
                "gear_only_mib_s": input_mib / (gear_ns / 1e9),
                "segmented_mib_s": input_mib / (segmented_ns / 1e9),
                "incremental_segmented_ns_per_input_byte": (segmented_ns - gear_ns) / len(data),
                "source_byte_rescans": 0,
            })
        return {
            "schema": "cmpct-one-g02-minimizer-segmented-residual-v1",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "purpose": "measure same-run residual encoder-discovery compute debt versus Gear-only recurrence; no promotion decision",
            "claim_boundary": "microkernel only; excludes exact proof, extension, Law selection, emission, wire and reader costs",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
