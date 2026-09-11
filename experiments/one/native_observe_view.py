"""ONE-G0.2 compact native observer handoff experiments.

These writer-side views preserve the existing native observer kernel while avoiding an
obligatory Python ``Observation`` object graph. ``NativeObservationView`` retains the
kernel's worst-case ctypes arenas. ``PackedObservationView`` is the rehabilitation path:
it copies only the used native records into exact-size byte strings, allowing the large
scratch arenas to die before downstream writer work. Neither view is reader-visible or a
persistence contract.
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


def _stats(s: _CStats) -> ObservationStats:
    return ObservationStats(
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
    )


@dataclass(slots=True)
class NativeObservationView:
    """Own worst-case native opportunity buffers without eagerly allocating Python opportunities."""

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

    @property
    def retained_output_bytes(self) -> int:
        return self.native_output_capacity_bytes

    def materialize(self) -> Observation:
        """Build the reference Python graph only when an oracle/debug consumer asks for it."""
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
            stats=_stats(self.cstats),
        )


@dataclass(slots=True)
class PackedObservationView:
    """Retain only the used native opportunity records after the observer scratch arenas die.

    The packed bytes are an internal transient handoff, not ONE wire syntax. Packing exports
    a copy proportional to discovered opportunities rather than source-size worst-case arena
    capacity. ``materialize`` reconstructs the reference Python objects for independent
    semantic checks without making them mandatory writer state.
    """

    runs_bytes: bytes
    reuse_bytes: bytes
    run_count: int
    reuse_count: int
    cstats: _CStats
    scratch_capacity_bytes: int

    @property
    def native_output_capacity_bytes(self) -> int:
        """Worst-case native scratch capacity required during the scan."""
        return self.scratch_capacity_bytes

    @property
    def native_output_used_bytes(self) -> int:
        return len(self.runs_bytes) + len(self.reuse_bytes)

    @property
    def retained_output_bytes(self) -> int:
        return self.native_output_used_bytes

    def materialize(self) -> Observation:
        run_array = (_CRun * self.run_count).from_buffer_copy(self.runs_bytes) if self.run_count else ()
        reuse_array = (_CReuse * self.reuse_count).from_buffer_copy(self.reuse_bytes) if self.reuse_count else ()
        return Observation(
            runs=tuple(
                RunOpportunity(int(run_array[i].start), int(run_array[i].length), int(run_array[i].value))
                for i in range(self.run_count)
            ),
            reuse=tuple(
                ReuseOpportunity(
                    int(reuse_array[i].source), int(reuse_array[i].target), int(reuse_array[i].length)
                )
                for i in range(self.reuse_count)
            ),
            stats=_stats(self.cstats),
        )


def _run_native(
    data: bytes,
    *,
    min_run: int,
    chunk_size: int,
    max_index_entries: int,
):
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
    return runs, reuse, int(run_count.value), int(reuse_count.value), stats, run_capacity, reuse_capacity


def observe_native_view(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> NativeObservationView:
    """Run the existing native observer and keep its worst-case output arenas alive."""
    runs, reuse, run_count, reuse_count, stats, run_capacity, reuse_capacity = _run_native(
        data,
        min_run=min_run,
        chunk_size=chunk_size,
        max_index_entries=max_index_entries,
    )
    return NativeObservationView(
        runs_buffer=runs,
        reuse_buffer=reuse,
        run_count=run_count,
        reuse_count=reuse_count,
        cstats=stats,
        run_capacity=run_capacity,
        reuse_capacity=reuse_capacity,
    )


def observe_native_packed(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> PackedObservationView:
    """Run the same native observer, then retain only exact used output prefixes.

    This intentionally pays one compact copy proportional to discovered opportunities so
    the source-sized worst-case ctypes arenas are not carried through the remainder of the
    writer. The copy is inside the candidate boundary and therefore cannot be hidden from
    timing.
    """
    runs, reuse, run_count, reuse_count, stats, run_capacity, reuse_capacity = _run_native(
        data,
        min_run=min_run,
        chunk_size=chunk_size,
        max_index_entries=max_index_entries,
    )
    run_width = ctypes.sizeof(_CRun)
    reuse_width = ctypes.sizeof(_CReuse)
    runs_used = run_count * run_width
    reuse_used = reuse_count * reuse_width
    runs_bytes = ctypes.string_at(ctypes.addressof(runs), runs_used) if runs_used else b""
    reuse_bytes = ctypes.string_at(ctypes.addressof(reuse), reuse_used) if reuse_used else b""
    return PackedObservationView(
        runs_bytes=runs_bytes,
        reuse_bytes=reuse_bytes,
        run_count=run_count,
        reuse_count=reuse_count,
        cstats=stats,
        scratch_capacity_bytes=run_capacity * run_width + reuse_capacity * reuse_width,
    )
