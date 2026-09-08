"""ONE-G0.2 compact native observer handoff experiment.

This module deliberately preserves the existing native observer kernel and its output
buffers while deferring construction of the Python ``Observation`` object graph.  It is
writer-side only: the view is not a reader-visible format, Law opcode, or persistence
contract.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass

from experiments.one.native_observe import _CRun, _CReuse, _CStats, _library
from experiments.one.observe import Observation, ObservationStats, ReuseOpportunity, RunOpportunity


def _validate(data: bytes, min_run: int, chunk_size: int, max_index_entries: int) -> None:
    if type(data) is not bytes:
        raise TypeError("ONE observation input must be bytes")
    for name, value in {
        "min_run": min_run,
        "chunk_size": chunk_size,
        "max_index_entries": max_index_entries,
    }.items():
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")


@dataclass(slots=True)
class NativeObservationView:
    """Own native opportunity buffers without eagerly allocating Python opportunities."""

    runs_buffer: object
    reuse_buffer: object
    run_count: int
    reuse_count: int
    cstats: _CStats
    run_capacity: int
    reuse_capacity: int

    @property
    def native_output_capacity_bytes(self) -> int:
        return self.run_capacity * ctypes.sizeof(_CRun) + self.reuse_capacity * ctypes.sizeof(_CReuse)

    @property
    def native_output_used_bytes(self) -> int:
        return self.run_count * ctypes.sizeof(_CRun) + self.reuse_count * ctypes.sizeof(_CReuse)

    def materialize(self) -> Observation:
        """Build the reference Python graph only when an oracle/debug consumer asks for it."""
        s = self.cstats
        return Observation(
            runs=tuple(
                RunOpportunity(
                    int(self.runs_buffer[i].start),
                    int(self.runs_buffer[i].length),
                    int(self.runs_buffer[i].value),
                )
                for i in range(self.run_count)
            ),
            reuse=tuple(
                ReuseOpportunity(
                    int(self.reuse_buffer[i].source),
                    int(self.reuse_buffer[i].target),
                    int(self.reuse_buffer[i].length),
                )
                for i in range(self.reuse_count)
            ),
            stats=ObservationStats(
                input_bytes=int(s.input_bytes),
                source_scan_bytes=int(s.source_scan_bytes),
                chunk_fingerprints=int(s.chunk_fingerprints),
                hash_lookups=int(s.hash_lookups),
                collision_verifications=int(s.collision_verifications),
                verification_read_bytes=int(s.verification_read_bytes),
                total_source_read_bytes=int(s.total_source_read_bytes),
                run_candidates=int(s.run_candidates),
                run_opportunity_bytes=int(s.run_opportunity_bytes),
                reuse_candidates=int(s.reuse_candidates),
                reuse_opportunity_bytes=int(s.reuse_opportunity_bytes),
                peak_index_entries=int(s.peak_index_entries),
                retained_index_payload_bytes=int(s.retained_index_payload_bytes),
            ),
        )


def observe_native_view(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> NativeObservationView:
    """Run the existing native observer and return its compact native outputs directly.

    Input copy, worst-case output allocation, the C kernel, and native statistics are
    intentionally identical in shape to ``observe_native``.  Only eager Python
    opportunity materialization is removed from this boundary.
    """
    _validate(data, min_run, chunk_size, max_index_entries)
    length = len(data)
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

    return NativeObservationView(
        runs_buffer=runs,
        reuse_buffer=reuse,
        run_count=int(run_count.value),
        reuse_count=int(reuse_count.value),
        cstats=stats,
        run_capacity=run_capacity,
        reuse_capacity=reuse_capacity,
    )
