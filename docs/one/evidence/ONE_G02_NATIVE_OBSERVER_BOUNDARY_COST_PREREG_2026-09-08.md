# ONE-G0.2 native observer boundary-cost decomposition — preregistration

Date: 2026-09-08
Scope: `research/cmpct1`, ONE-G0.2

## Mission lock

The exact-source whole-writer profiler now identifies `native_observe` as a repeated 1 MiB stage owner. That timing currently includes more than the C observation loop: Python allocates worst-case result arrays, copies the immutable input into a ctypes-owned buffer, invokes the kernel, and materializes Python `Observation` objects.

Do not optimize the C scan until this boundary cost is decomposed. The speed law requires attacking the actual owner, not the label attached to a timing region.

## Referee hypothesis

At 1 MiB, a material fraction of current `observe_native()` wall/CPU time is outside the C observation kernel, with the strongest suspects being worst-case output-buffer allocation/zeroing and Python boundary preparation rather than input copying alone.

### Disproof

The hypothesis is disproved if a preallocated, zero-copy-input kernel call accounts for at least 90% of current full-wrapper median wall and CPU time on every tested family. In that case the C kernel itself is the clear owner and wrapper work is secondary.

## Frozen matrix

Sizes: 256 KiB and 1 MiB.

Families reuse the existing native-observer generators:

- structured;
- seeded incompressible/random;
- compressed-like;
- long runs;
- near repeats.

Repetitions: 15, paired alternating where two paths are compared.

Compilation/warm-up occurs outside timed samples.

## Decomposition

For identical input bytes and unchanged observer parameters measure:

1. `full_wrapper`: current public `observe_native()` end to end;
2. `input_copy`: current `(ctypes.c_uint8 * length).from_buffer_copy(data)` only;
3. `output_allocation`: current worst-case `_CRun` and `_CReuse` array allocation only;
4. `kernel_preallocated_zero_copy`: `one_observe_native` using a read-only CPython bytes pointer plus preallocated result arrays;
5. `marshal_only`: convert already-populated C outputs/stats into the same Python `Observation` value, without rerunning the kernel.

The zero-copy pointer is experimental benchmark machinery only. It may not be promoted into the writer merely because it is faster; semantic parity, lifetime safety and portability must be established separately.

All kernel calls must exactly match `observe_native()` output and statistics.

## Derived quantities

For each row report:

- median wall/CPU ns for every component;
- `kernel/full_wrapper` wall and CPU ratios;
- `(input_copy + output_allocation + marshal)/full_wrapper` descriptive ratios;
- actual run/reuse counts;
- allocated output-buffer bytes versus used output bytes.

The component medians are not assumed additive because allocator/cache interactions exist. The ratio is causal guidance, not a reconstructed timer.

## Decision

- `KERNEL_DOMINATES_NATIVE_OBSERVER` if preallocated zero-copy kernel wall **and** CPU are >=0.90x full wrapper on every row.
- `BOUNDARY_COST_MATERIAL` otherwise, provided semantic parity holds everywhere.
- `INVALID_NATIVE_OBSERVER_BOUNDARY_DECOMPOSITION` on any semantic/stat mismatch or kernel error.

A boundary-cost result does not itself authorize a production optimization. It chooses the next falsifier:

- allocation dominates -> test bounded/reusable output arenas or tighter capacities;
- input copy dominates -> test safe read-only zero-copy binding;
- marshalling dominates -> test compact native discovery state consumed directly by downstream writer stages;
- kernel dominates -> profile/index/scan the C loop itself.

## Claim boundary

Writer-side component attribution only. No stored-byte, reader, format, comparator, v0.29/v0.30, or canonical release authority.