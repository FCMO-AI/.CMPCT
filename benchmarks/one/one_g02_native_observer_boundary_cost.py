"""ONE-G0.2 native observer boundary-cost falsifier.

Preregistered by ONE_G02_NATIVE_OBSERVER_BOUNDARY_COST_PREREG_2026-09-08.md.
Writer-side attribution only; no representation or comparator authority.
"""
from __future__ import annotations

import ctypes
import gc
import json
import os
import statistics
import time

from benchmarks.one.one_g02_native_fresh_observer import FAMILIES
from experiments.one.native_observe import _CRun, _CReuse, _CStats, _library, observe_native
from experiments.one.observe import Observation, ObservationStats, ReuseOpportunity, RunOpportunity

SIZES = (256 << 10, 1 << 20)
REPETITIONS = 15
MIN_RUN = 8
CHUNK_SIZE = 64
MAX_INDEX_ENTRIES = 1 << 16
KERNEL_DOMINANCE = 0.90

_PYBYTES_AS_STRING = ctypes.pythonapi.PyBytes_AsString
_PYBYTES_AS_STRING.argtypes = [ctypes.py_object]
_PYBYTES_AS_STRING.restype = ctypes.c_void_p


def _capacities(length: int) -> tuple[int, int]:
    return max(1, length // MIN_RUN + 2), max(1, length // CHUNK_SIZE + 2)


def _zero_copy_ptr(data: bytes):
    address = _PYBYTES_AS_STRING(data)
    if not address and data:
        raise RuntimeError("PyBytes_AsString returned NULL")
    return ctypes.cast(address, ctypes.POINTER(ctypes.c_uint8)) if data else ctypes.POINTER(ctypes.c_uint8)()


def _allocate_outputs(length: int):
    run_capacity, reuse_capacity = _capacities(length)
    return (
        (_CRun * run_capacity)(),
        (_CReuse * reuse_capacity)(),
        ctypes.c_size_t(),
        ctypes.c_size_t(),
        _CStats(),
        run_capacity,
        reuse_capacity,
    )


def _call_kernel(data: bytes, source_ptr, state) -> None:
    runs, reuse, run_count, reuse_count, stats, run_capacity, reuse_capacity = state
    rc = _library().one_observe_native(
        source_ptr,
        len(data),
        MIN_RUN,
        CHUNK_SIZE,
        MAX_INDEX_ENTRIES,
        runs,
        run_capacity,
        ctypes.byref(run_count),
        reuse,
        reuse_capacity,
        ctypes.byref(reuse_count),
        ctypes.byref(stats),
    )
    if rc != 0:
        raise RuntimeError(f"native ONE observer failed with status {rc}")


def _marshal(state) -> Observation:
    runs, reuse, run_count, reuse_count, stats, _run_capacity, _reuse_capacity = state
    return Observation(
        runs=tuple(
            RunOpportunity(int(runs[i].start), int(runs[i].length), int(runs[i].value))
            for i in range(run_count.value)
        ),
        reuse=tuple(
            ReuseOpportunity(int(reuse[i].source), int(reuse[i].target), int(reuse[i].length))
            for i in range(reuse_count.value)
        ),
        stats=ObservationStats(
            input_bytes=int(stats.input_bytes),
            source_scan_bytes=int(stats.source_scan_bytes),
            chunk_fingerprints=int(stats.chunk_fingerprints),
            hash_lookups=int(stats.hash_lookups),
            collision_verifications=int(stats.collision_verifications),
            verification_read_bytes=int(stats.verification_read_bytes),
            total_source_read_bytes=int(stats.total_source_read_bytes),
            run_candidates=int(stats.run_candidates),
            run_opportunity_bytes=int(stats.run_opportunity_bytes),
            reuse_candidates=int(stats.reuse_candidates),
            reuse_opportunity_bytes=int(stats.reuse_opportunity_bytes),
            peak_index_entries=int(stats.peak_index_entries),
            retained_index_payload_bytes=int(stats.retained_index_payload_bytes),
        ),
    )


def _median_timing(fn):
    wall = []
    cpu = []
    last = None
    for _ in range(REPETITIONS):
        c0 = time.process_time_ns()
        w0 = time.perf_counter_ns()
        last = fn()
        w1 = time.perf_counter_ns()
        c1 = time.process_time_ns()
        wall.append(w1 - w0)
        cpu.append(c1 - c0)
    return float(statistics.median(wall)), float(statistics.median(cpu)), last


def run():
    # Build and resolve all dynamic symbols outside timed regions.
    observe_native(b"warmup" * 32)
    _library()
    rows = []
    semantic_ok = True
    kernel_dominates_everywhere = True

    was_enabled = gc.isenabled()
    try:
        if was_enabled:
            gc.disable()
        for size in SIZES:
            for family, builder in FAMILIES.items():
                data = builder(size)
                expected = observe_native(data)
                source_ptr = _zero_copy_ptr(data)
                state = _allocate_outputs(size)
                _call_kernel(data, source_ptr, state)
                raw_value = _marshal(state)
                same = raw_value == expected
                semantic_ok &= same
                if not same:
                    raise AssertionError(f"zero-copy/preallocated semantic divergence: {size=} {family=}")

                # Pair the current public wrapper against the isolated kernel to reduce
                # systematic order/thermal bias on the decision-bearing ratio.
                full_wall = []
                full_cpu = []
                kernel_wall = []
                kernel_cpu = []
                for rep in range(REPETITIONS):
                    labels = ("full", "kernel") if rep % 2 == 0 else ("kernel", "full")
                    for label in labels:
                        c0 = time.process_time_ns()
                        w0 = time.perf_counter_ns()
                        if label == "full":
                            result = observe_native(data)
                        else:
                            _call_kernel(data, source_ptr, state)
                            result = None
                        w1 = time.perf_counter_ns()
                        c1 = time.process_time_ns()
                        if label == "full":
                            if result != expected:
                                raise AssertionError(f"timed full-wrapper divergence: {size=} {family=}")
                            full_wall.append(w1 - w0)
                            full_cpu.append(c1 - c0)
                        else:
                            kernel_wall.append(w1 - w0)
                            kernel_cpu.append(c1 - c0)

                fwall = float(statistics.median(full_wall))
                fcpu = float(statistics.median(full_cpu))
                kwall = float(statistics.median(kernel_wall))
                kcpu = float(statistics.median(kernel_cpu))

                copy_wall, copy_cpu, _ = _median_timing(
                    lambda: (ctypes.c_uint8 * size).from_buffer_copy(data)
                )
                alloc_wall, alloc_cpu, _ = _median_timing(lambda: _allocate_outputs(size))
                # Refresh the state once before repeatedly measuring Python materialization.
                _call_kernel(data, source_ptr, state)
                marshal_wall, marshal_cpu, marshaled = _median_timing(lambda: _marshal(state))
                if marshaled != expected:
                    raise AssertionError(f"marshal-only divergence: {size=} {family=}")

                kernel_wall_ratio = kwall / fwall
                kernel_cpu_ratio = kcpu / fcpu
                row_kernel_dominates = kernel_wall_ratio >= KERNEL_DOMINANCE and kernel_cpu_ratio >= KERNEL_DOMINANCE
                kernel_dominates_everywhere &= row_kernel_dominates

                run_capacity, reuse_capacity = _capacities(size)
                allocated_output_bytes = (
                    run_capacity * ctypes.sizeof(_CRun) + reuse_capacity * ctypes.sizeof(_CReuse)
                )
                used_output_bytes = (
                    int(state[2].value) * ctypes.sizeof(_CRun) + int(state[3].value) * ctypes.sizeof(_CReuse)
                )
                rows.append({
                    "size": size,
                    "family": family,
                    "full_wrapper_wall_ns": fwall,
                    "full_wrapper_cpu_ns": fcpu,
                    "kernel_preallocated_zero_copy_wall_ns": kwall,
                    "kernel_preallocated_zero_copy_cpu_ns": kcpu,
                    "input_copy_wall_ns": copy_wall,
                    "input_copy_cpu_ns": copy_cpu,
                    "output_allocation_wall_ns": alloc_wall,
                    "output_allocation_cpu_ns": alloc_cpu,
                    "marshal_wall_ns": marshal_wall,
                    "marshal_cpu_ns": marshal_cpu,
                    "kernel_over_full_wall_ratio": kernel_wall_ratio,
                    "kernel_over_full_cpu_ratio": kernel_cpu_ratio,
                    "descriptive_boundary_sum_over_full_wall_ratio": (copy_wall + alloc_wall + marshal_wall) / fwall,
                    "descriptive_boundary_sum_over_full_cpu_ratio": (copy_cpu + alloc_cpu + marshal_cpu) / fcpu,
                    "kernel_dominates_row": row_kernel_dominates,
                    "runs": len(expected.runs),
                    "reuse": len(expected.reuse),
                    "run_capacity": run_capacity,
                    "reuse_capacity": reuse_capacity,
                    "allocated_output_bytes": allocated_output_bytes,
                    "used_output_bytes": used_output_bytes,
                    "allocated_over_used_output_ratio": (
                        allocated_output_bytes / used_output_bytes if used_output_bytes else None
                    ),
                    "semantic_exact": same,
                })
    finally:
        if was_enabled:
            gc.enable()

    if not semantic_ok:
        decision = "INVALID_NATIVE_OBSERVER_BOUNDARY_DECOMPOSITION"
    elif kernel_dominates_everywhere:
        decision = "KERNEL_DOMINATES_NATIVE_OBSERVER"
    else:
        decision = "BOUNDARY_COST_MATERIAL"
    return {
        "schema": "cmpct-one-g02-native-observer-boundary-cost-v1",
        "experimental_version": "ONE-G0.2",
        "source_sha": os.environ.get("EVIDENCE_HEAD") or os.environ.get("GITHUB_SHA") or "local-unbound",
        "sizes": list(SIZES),
        "families": list(FAMILIES),
        "repetitions": REPETITIONS,
        "kernel_dominance_threshold": KERNEL_DOMINANCE,
        "semantic_gates_pass": semantic_ok,
        "decision": decision,
        "claim_boundary": (
            "writer-side native-observer boundary attribution only; CPython zero-copy pointer is benchmark machinery, "
            "not a promoted binding; no stored-byte, reader, format, release or comparator authority"
        ),
        "rows": rows,
    }


if __name__ == "__main__":
    result = run()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(1 if result["decision"].startswith("INVALID") else 0)
