"""ONE-G0.2 compiled probe for the Gear/rightmost-minimum selector recurrence.

This is deliberately a research microkernel, not native ONE production work. It asks whether
the ~4x Python slowdown is structural to the selector or mostly interpreter/deque overhead.
The compiled experiment separates three costs: unavoidable Gear formation, Gear + rolling
minimum maintenance, and Python-to-C input copying. Exact reuse verification, extension,
indexing and Law-cost accounting remain outside this probe and therefore cannot be hidden
inside a speed claim.
"""
from __future__ import annotations

from collections import deque
import ctypes
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import tempfile
import time
import zlib

from benchmarks.one.one_g02_gear_replacement_ab import _GEAR, WINDOW, _U64_MASK
from benchmarks.one.one_g02_minimizer_gear_ab import MINIMIZER_SPAN

REPETITIONS = 9
SIZE = 1024 * 1024


class _KernelResult(ctypes.Structure):
    _fields_ = [
        ("emitted", ctypes.c_uint64),
        ("peak_queue", ctypes.c_uint64),
        ("final_state", ctypes.c_uint64),
        ("positions_considered", ctypes.c_uint64),
    ]


def _python_recurrence(data: bytes) -> tuple[int, int, int, int]:
    minima: deque[tuple[int, int]] = deque()
    enabled = len(data) >= MINIMIZER_SPAN + WINDOW
    h = 0
    peak = emitted = considered = 0
    last_emitted = -1
    for position, value in enumerate(data):
        h = ((h << 1) + _GEAR[value]) & _U64_MASK
        if position + 1 < WINDOW:
            continue
        considered += 1
        if not enabled:
            continue
        while minima and minima[-1][0] >= h:
            minima.pop()
        minima.append((h, position))
        first_valid = position - MINIMIZER_SPAN + 1
        while minima and minima[0][1] < first_valid:
            minima.popleft()
        peak = max(peak, len(minima))
        if first_valid < WINDOW - 1:
            continue
        anchor_position = minima[0][1]
        if anchor_position != last_emitted:
            last_emitted = anchor_position
            emitted += 1
    return emitted, peak, h, considered


def _build_kernel() -> tuple[ctypes.CDLL, tempfile.TemporaryDirectory[str]]:
    source = Path(__file__).with_name("one_g02_minimizer_kernel.c")
    tempdir = tempfile.TemporaryDirectory(prefix="cmpct-one-g02-")
    library = Path(tempdir.name) / "libone_g02_minimizer.so"
    command = [
        os.environ.get("CC", "cc"),
        "-O3",
        "-std=c11",
        "-fPIC",
        "-shared",
        str(source),
        "-o",
        str(library),
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ctypes.CDLL(str(library)), tempdir


def _bind(lib: ctypes.CDLL):
    minimizer = lib.one_g02_minimizer_kernel
    minimizer.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    minimizer.restype = ctypes.c_int
    gear_only = lib.one_g02_gear_only_kernel
    gear_only.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64),
        ctypes.c_size_t, ctypes.POINTER(_KernelResult),
    ]
    gear_only.restype = ctypes.c_int
    return minimizer, gear_only


def _minimizer_call(fn, gear, data_array, length: int) -> _KernelResult:
    out = _KernelResult()
    rc = fn(data_array, length, gear, WINDOW, MINIMIZER_SPAN, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"ONE-G0.2 native minimizer kernel failed: {rc}")
    return out


def _gear_call(fn, gear, data_array, length: int) -> _KernelResult:
    out = _KernelResult()
    rc = fn(data_array, length, gear, WINDOW, ctypes.byref(out))
    if rc != 0:
        raise RuntimeError(f"ONE-G0.2 native Gear kernel failed: {rc}")
    return out


def _native_with_copy(fn, gear, data: bytes) -> _KernelResult:
    data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
    return _minimizer_call(fn, gear, data_array, len(data))


def _median_ns(fn) -> tuple[int, object]:
    samples: list[int] = []
    last = None
    for _ in range(REPETITIONS):
        start = time.perf_counter_ns()
        last = fn()
        samples.append(time.perf_counter_ns() - start)
    return int(statistics.median(samples)), last


def _cases() -> dict[str, bytes]:
    random_1m = random.Random(7101).randbytes(SIZE)
    source_512k = random.Random(7102).randbytes(SIZE // 2)
    starved = random.Random(4876).randbytes(8 * 1024)
    repeated_basis = random.Random(7103).randbytes(64 * 1024)
    boundary = random.Random(7104).randbytes(MINIMIZER_SPAN + WINDOW)
    return {
        "below_enablement_4159b": boundary[:-1],
        "at_enablement_4160b": boundary,
        "random_1mib": random_1m,
        "zlib_random_1mib": zlib.compress(random_1m, level=9),
        "exact_pair_512k": source_512k + source_512k,
        "shifted_pair_512k_insert1": source_512k + b"X" + source_512k,
        "repeated_64k_basis_1mib": repeated_basis * 16,
        "starved_shifted_8k_insert1": starved + b"X" + starved,
    }


def run() -> dict[str, object]:
    lib, tempdir = _build_kernel()
    try:
        minimizer_fn, gear_fn = _bind(lib)
        gear = (ctypes.c_uint64 * 256)(*_GEAR)
        rows: list[dict[str, object]] = []
        for name, data in _cases().items():
            py_expected = _python_recurrence(data)
            data_array = (ctypes.c_uint8 * len(data)).from_buffer_copy(data)
            native_once = _minimizer_call(minimizer_fn, gear, data_array, len(data))
            native_tuple = (
                int(native_once.emitted), int(native_once.peak_queue),
                int(native_once.final_state), int(native_once.positions_considered),
            )
            if native_tuple != py_expected:
                raise AssertionError(
                    f"native recurrence mismatch for {name}: native={native_tuple} python={py_expected}"
                )
            gear_once = _gear_call(gear_fn, gear, data_array, len(data))
            if int(gear_once.final_state) != py_expected[2] or int(gear_once.positions_considered) != py_expected[3]:
                raise AssertionError(f"Gear-only semantic mismatch for {name}")

            python_ns, _ = _median_ns(lambda: _python_recurrence(data))
            gear_ns, _ = _median_ns(lambda: _gear_call(gear_fn, gear, data_array, len(data)))
            kernel_ns, checked = _median_ns(
                lambda: _minimizer_call(minimizer_fn, gear, data_array, len(data))
            )
            with_copy_ns, _ = _median_ns(lambda: _native_with_copy(minimizer_fn, gear, data))
            assert isinstance(checked, _KernelResult)
            mib = len(data) / (1024 * 1024)
            rows.append(
                {
                    "case": name,
                    "input_bytes": len(data),
                    "emitted_minimizers": native_tuple[0],
                    "peak_queue_entries": native_tuple[1],
                    "reserved_kernel_state_bytes": MINIMIZER_SPAN * 16 + 256 * 8,
                    "observed_peak_state_payload_bytes": native_tuple[1] * 16 + 256 * 8,
                    "python_median_ns": python_ns,
                    "native_gear_only_median_ns": gear_ns,
                    "native_kernel_median_ns": kernel_ns,
                    "native_with_input_copy_median_ns": with_copy_ns,
                    "native_gear_only_mib_per_second": mib / (gear_ns / 1e9),
                    "native_kernel_mib_per_second": mib / (kernel_ns / 1e9),
                    "native_with_copy_mib_per_second": mib / (with_copy_ns / 1e9),
                    "minimizer_elapsed_ratio_over_gear_only": kernel_ns / gear_ns,
                    "incremental_minimizer_ns_per_input_byte": (kernel_ns - gear_ns) / len(data),
                    "compiled_kernel_speedup_over_python_recurrence": python_ns / kernel_ns,
                }
            )
        return {
            "schema": "cmpct-one-g02-minimizer-native-probe-v4",
            "experimental_version": "ONE-G0.2",
            "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
            "repetitions": REPETITIONS,
            "window": WINDOW,
            "minimizer_span": MINIMIZER_SPAN,
            "hypothesis": "the Gear/rightmost-minimum selector has a credible compiled cost path and the observed Python slowdown is not primarily structural algorithmic cost",
            "disproof": "native recurrence disagrees with Python semantics, requires unbounded state, or rolling-minimum maintenance remains an excessive multiplier over the same compiled Gear recurrence",
            "claim_boundary": "research microkernel only; Gear-only, minimizer, and Python-to-C-copy costs are separated; excludes exact-proof, extension, index and Law construction costs and is not product/native-reader authority",
            "rows": rows,
        }
    finally:
        tempdir.cleanup()


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
