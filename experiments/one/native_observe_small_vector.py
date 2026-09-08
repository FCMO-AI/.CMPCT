"""ONE-G0.2 one-slot small-vector native observer handoff.

Zero/one discovered opportunity avoids a bulk-prefix byte allocation; two or more use
the established packed representation. This is transient writer state only.
"""
from __future__ import annotations

import ctypes
from dataclasses import dataclass

from experiments.one.native_observe import _CRun, _CReuse, _CStats
from experiments.one.native_observe_view import _run_native, _stats
from experiments.one.observe import Observation, ReuseOpportunity, RunOpportunity


@dataclass(slots=True)
class SmallVectorObservationView:
    run_count: int
    reuse_count: int
    cstats: _CStats
    scratch_capacity_bytes: int
    inline_kind: int  # 0 empty/bulk, 1 run, 2 reuse
    inline_a: int
    inline_b: int
    inline_c: int
    runs_bytes: bytes
    reuse_bytes: bytes

    @property
    def total_count(self) -> int:
        return self.run_count + self.reuse_count

    @property
    def uses_inline_slot(self) -> bool:
        return self.total_count == 1

    @property
    def uses_bulk_bytes(self) -> bool:
        return self.total_count > 1

    @property
    def native_output_capacity_bytes(self) -> int:
        return self.scratch_capacity_bytes

    @property
    def native_output_used_bytes(self) -> int:
        return self.total_count * 3 * ctypes.sizeof(ctypes.c_uint64)

    @property
    def retained_output_bytes(self) -> int:
        return self.native_output_used_bytes

    def materialize(self) -> Observation:
        if self.total_count == 0:
            runs = ()
            reuse = ()
        elif self.inline_kind == 1:
            runs = (RunOpportunity(self.inline_a, self.inline_b, self.inline_c),)
            reuse = ()
        elif self.inline_kind == 2:
            runs = ()
            reuse = (ReuseOpportunity(self.inline_a, self.inline_b, self.inline_c),)
        else:
            run_array = (_CRun * self.run_count).from_buffer_copy(self.runs_bytes) if self.run_count else ()
            reuse_array = (_CReuse * self.reuse_count).from_buffer_copy(self.reuse_bytes) if self.reuse_count else ()
            runs = tuple(
                RunOpportunity(int(run_array[i].start), int(run_array[i].length), int(run_array[i].value))
                for i in range(self.run_count)
            )
            reuse = tuple(
                ReuseOpportunity(int(reuse_array[i].source), int(reuse_array[i].target), int(reuse_array[i].length))
                for i in range(self.reuse_count)
            )
        return Observation(runs=runs, reuse=reuse, stats=_stats(self.cstats))


def observe_native_small_vector(
    data: bytes,
    *,
    min_run: int = 8,
    chunk_size: int = 64,
    max_index_entries: int = 1 << 16,
) -> SmallVectorObservationView:
    runs, reuse, run_count, reuse_count, stats, run_capacity, reuse_capacity = _run_native(
        data,
        min_run=min_run,
        chunk_size=chunk_size,
        max_index_entries=max_index_entries,
    )
    run_width = ctypes.sizeof(_CRun)
    reuse_width = ctypes.sizeof(_CReuse)
    scratch = run_capacity * run_width + reuse_capacity * reuse_width
    total = run_count + reuse_count

    inline_kind = inline_a = inline_b = inline_c = 0
    runs_bytes = b""
    reuse_bytes = b""
    if total == 1:
        if run_count == 1:
            record = runs[0]
            inline_kind = 1
            inline_a = int(record.start)
            inline_b = int(record.length)
            inline_c = int(record.value)
        else:
            record = reuse[0]
            inline_kind = 2
            inline_a = int(record.source)
            inline_b = int(record.target)
            inline_c = int(record.length)
    elif total > 1:
        runs_used = run_count * run_width
        reuse_used = reuse_count * reuse_width
        runs_bytes = ctypes.string_at(ctypes.addressof(runs), runs_used) if runs_used else b""
        reuse_bytes = ctypes.string_at(ctypes.addressof(reuse), reuse_used) if reuse_used else b""

    return SmallVectorObservationView(
        run_count=run_count,
        reuse_count=reuse_count,
        cstats=stats,
        scratch_capacity_bytes=scratch,
        inline_kind=inline_kind,
        inline_a=inline_a,
        inline_b=inline_b,
        inline_c=inline_c,
        runs_bytes=runs_bytes,
        reuse_bytes=reuse_bytes,
    )
