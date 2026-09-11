# ONE-G0.2 lazy native segment-arena falsifier — 2026-09-08

## Mission lock / referee

The packed-observer fresh-process RSS gate at exact source `0778b989bc5d3ab5bd1d1290193d02283a8c7365` was censored by a 93,460 KiB pre-writer high-water mark. One concrete common-state owner is the native segment output arena: the current research harness allocates `(Segment * source_bytes)()` before relation admission, even though segmentation is executed only when admission succeeds.

On the hosted ABI `Segment` occupies 12 bytes, so a 1 MiB source reserves ~12 MiB before the writer knows whether that memory is useful.

This experiment asks whether segment state should be allocated **after** relation admission, without changing the native segmenter, relation law, Program, wire, reader or hard semantics.

## Candidate and control

Control:

`source/target ctypes -> allocate maximum Segment arena -> relation admission -> segment if enabled -> Program -> validate -> emit`

Candidate:

`source/target ctypes -> relation admission -> allocate maximum Segment arena only if enabled -> segment -> Program -> validate -> emit`

Both arms still allocate the same maximum segment capacity on admitted cases. This falsifier tests lifetime/opportunity gating only; it does not yet solve worst-case admitted-plan capacity.

## Frozen matrix

Size: 1 MiB.

Use exact deterministic temporal relation cases from `_relation_cases(1 << 20)`:

- admitted: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- rejected controls: `fragmented_every32`, `independent_random`.

Use 7 fresh child processes per arm/case, alternating launch order.

## Falsifiable hypothesis

Rejected cases should avoid the ~12 MiB segment arena entirely and therefore reduce live/current RSS by at least **8 MiB** at the post-admission/pre-Program checkpoint without changing semantics. Admitted cases must retain exact segment-plan and wire semantics and may not increase fresh-process peak RSS by >5%.

Disproof:

- any semantic mismatch invalidates the candidate;
- either rejected control saving <8 MiB at the causal checkpoint blocks the memory mechanism claim;
- any admitted case candidate/control peak RSS >1.05 blocks promotion;
- any admitted case plan/wire mismatch invalidates promotion.

## Measurements

Each child reports Linux `/proc/self/status` current `VmRSS` and `VmHWM` at:

1. after source/target ctypes arrays are built;
2. after eager segment allocation or the equivalent lazy no-op;
3. after relation admission;
4. after candidate segment allocation if admitted;
5. after segmentation/Program/emission.

Also report `ru_maxrss`, segment ABI width/capacity bytes, relation enable/proof count, segment count, canonical wire bytes, Surprise bytes, and exact reconstruction.

Process startup/import time does not vote. Allocation and writer semantics do.

## Frozen decisions

`ADVANCE_LAZY_SEGMENT_ARENA` requires:

- exact semantics on all five cases;
- both rejected cases save >=8 MiB current RSS at the post-admission checkpoint versus eager;
- every admitted case median lazy/eager final peak RSS <=1.05;
- rejected cases allocate exactly zero segment-capacity bytes in the candidate;
- admitted candidate segment capacity equals the control capacity.

Otherwise return `HOLD_LAZY_SEGMENT_ARENA`; any semantic disagreement returns `INVALIDATE_LAZY_SEGMENT_ARENA`.

## Claim boundary / hostile review

- This is writer resource scheduling, not a ONE opcode or stored-format change.
- A pass does not prove the admitted maximum segment arena is well-sized; it only stops paying it when segmentation is impossible/unused.
- Do not compare a rejected candidate to an admitted control; relation decisions must be identical.
- Do not use `ru_maxrss` alone; the previous experiment showed that an earlier common peak can censor the causal effect.
- Current `VmRSS` is allocator/OS-sensitive. The >=8 MiB floor is intentionally large relative to the ~12 MiB arena and requires both rejected controls.
- No speed win is required or claimed here. A later whole-writer timing gate must charge lazy allocation placement if this becomes a production path.
- No v0.29/deferred-v0.30 Genesis authority is earned.
