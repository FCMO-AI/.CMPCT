# ONE-G0.2 packed observer fresh-process RSS gate — 2026-09-08

## Mission lock / referee

Exact-source run `34219617441` at `49dce83b186505bff462f3971e81236e6a49bfe1` returned `ADVANCE_PACKED_OBSERVER_REHABILITATION`. The 1 MiB packed/eager wall ratios were 0.3480x structured, 0.9184x compressed-like, 0.9075x long-runs, 0.9956x random and 1.0041x near-repeats, with exact semantics and every 1 MiB row under the frozen 1.05 ceiling.

The pass does **not** establish a memory improvement. Both arms still allocate the same worst-case observer scratch arena during the C scan (~3.54 MiB at a 1 MiB source), and the whole-writer harness also owns other substantial transient state. The packed arm merely shortens observer-arena lifetime and replaces eager Python opportunity objects with exact-size packed records.

This gate measures process peak RSS in fresh child processes before any broader promotion.

## Regression debt preserved

The same packed artifact contains non-voting 256 KiB regressions that remain active debt:

- `compressed_like`: 1.1264x wall / 1.1262x CPU;
- `long_runs`: 1.0879x wall / 1.0877x CPU.

Do not hide those rows behind a newly invented size threshold. This RSS gate does not rehabilitate them. A later dense-size/crossover falsifier must decide whether they are stable mechanism cost or hosted-runtime variance before a general writer claim.

## Falsifiable hypothesis

In fresh 1 MiB writer processes, replacing eager Python opportunity materialization with packed used-prefix state will not increase median peak RSS materially on any frozen family, and may reduce peak RSS on the 12,288-opportunity structured family.

Disproof: any family with median packed/eager peak RSS >1.05 blocks an RSS-safe promotion. A measured structured reduction is reported only if <=0.95; otherwise memory is treated as parity even if speed remains strong.

## Frozen matrix

- size: 1 MiB only;
- families: `structured`, `compressed_like`, `long_runs`, `random`, `near_repeats` from the rehabilitation benchmark;
- 7 independent fresh child processes per arm/family;
- alternate eager/packed child launch order by repetition;
- each child compiles/loads the same native libraries, constructs the same source/target and writer buffers, executes one complete charged research-writer call, verifies byte-exact reconstruction, then reports `resource.getrusage(RUSAGE_SELF).ru_maxrss`;
- hosted Linux units are KiB and are recorded explicitly.

Process startup wall time does not vote. The writer result and semantic gates do.

## Hard semantic gates

For every arm/family child:

1. writer completes without native error;
2. canonical wire decodes successfully;
3. previous/current outputs reconstruct byte-exactly;
4. root digests remain exact;
5. packed authority materialization equals `observe_native()` on the same target in an untimed parent authority path.

Any disagreement returns `INVALIDATE_PACKED_OBSERVER_RSS_GATE`.

## Frozen RSS decision

- every family median packed/eager peak RSS <= **1.05**;
- `structured` is separately labeled `STRUCTURED_RSS_REDUCTION` only if its ratio <= **0.95**;
- ratios 0.95–1.05 are memory parity, not a claimed win.

Decisions:

- `ADVANCE_PACKED_OBSERVER_RSS_SAFE` if semantics are exact and all five families are <=1.05;
- `HOLD_PACKED_OBSERVER_RSS` if semantics are exact but any family exceeds 1.05;
- `INVALIDATE_PACKED_OBSERVER_RSS_GATE` on semantic failure.

## Claim boundary

A pass says only that the packed writer-internal handoff is not materially worse in fresh-process peak RSS on this 1 MiB matrix. It does not remove the ~3.54 MiB scan scratch peak, solve the oversized native Segment buffer, prove product memory bounds, fix the 256 KiB speed debt, make downstream admission consume observation, change stored bytes/reader semantics, or earn v0.29/deferred-v0.30 Genesis authority.
