"""ctypes wrapper for the ONE-G0.2 native fresh-observation candidate."""
from __future__ import annotations

import ctypes
from functools import lru_cache
from pathlib import Path
import subprocess
import tempfile

from experiments.one.observe import (
    Observation,
    ObservationStats,
    ReuseOpportunity,
    RunOpportunity,
)


class _CRun(ctypes.Structure):
    _fields_ = [("start", ctypes.c_uint64), ("length", ctypes.c_uint64), ("value", ctypes.c_uint64)]


class _CReuse(ctypes.Structure):
    _fields_ = [("source", ctypes.c_uint64), ("target", ctypes.c_uint64), ("length", ctypes.c_uint64)]


class _CStats(ctypes.Structure):
    _fields_ = [
        ("input_bytes", ctypes.c_uint64),
        ("source_scan_bytes", ctypes.c_uint64),
        ("chunk_fingerprints", ctypes.c_uint64),
        ("hash_lookups", ctypes.c_uint64),
        ("collision_verifications", ctypes.c_uint64),
        ("verification_read_bytes", ctypes.c_uint64),
        ("total_source_read_bytes", ctypes.c_uint64),
        ("run_candidates", ctypes.c_uint64),
        ("run_opportunity_bytes", ctypes.c_uint64),
        ("reuse_candidates", ctypes.c_uint64),
        ("reuse_opportunity_bytes", ctypes.c_uint64),
        ("peak_index_entries", ctypes.c_uint64),
        ("retained_index_payload_bytes", ctypes.c_uint64),
    ]


@lru_cache(maxsize=1)
def _library() -> ctypes.CDLL:
    source = Path(__file__).with_name("native_observe_kernel.c")
    build_dir = Path(tempfile.mkdtemp(prefix="cmpct-one-native-observe-"))
    output = build_dir / "libone_native_observe.so"
    subprocess.run(
        ["cc", "-O3", "-std=c11", "-fPIC", "-shared", str(source), "-o", str(output)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    lib = ctypes.CDLL(str(output))
    fn = lib.one_observe_native
    fn.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t,
        ctypes.c_uint64,
        ctypes.c_uint64,
        ctypes.c_uint64,
        ctypes.POINTER(_CRun),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(_CReuse),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(_CStats),
    ]
    fn.restype = ctypes.c_int
    return lib


def observe_native(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> Observation:
    if type(data) is not bytes:
        raise TypeError("ONE observation input must be bytes")
    for name, value in {
        "min_run": min_run,
        "chunk_size": chunk_size,
        "max_index_entries": max_index_entries,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")

    length = len(data)
    # Qualifying maximal runs require at least min_run bytes each; reuse outputs cannot
    # outnumber complete fingerprint chunks. Add small guards for empty/tail inputs.
    run_capacity = max(1, length // min_run + 2)
    reuse_capacity = max(1, length // chunk_size + 2)
    runs = (_CRun * run_capacity)()
    reuse = (_CReuse * reuse_capacity)()
    run_count = ctypes.c_size_t()
    reuse_count = ctypes.c_size_t()
    stats = _CStats()
    if length:
        source = (ctypes.c_uint8 * length).from_buffer_copy(data)
        source_ptr = ctypes.cast(source, ctypes.POINTER(ctypes.c_uint8))
    else:
        source = None
        source_ptr = ctypes.POINTER(ctypes.c_uint8)()

    rc = _library().one_observe_native(
        source_ptr,
        length,
        min_run,
        chunk_size,
        max_index_entries,
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
