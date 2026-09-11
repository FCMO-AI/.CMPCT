# ONE-G0.2 lazy segment-arena whole-writer timing gate — 2026-09-08

## Mission lock / referee

Exact-source memory run `34220784946` demonstrated that allocation-after-admission removes ~12.2–12.4 MiB of dead current RSS and ~26% of peak RSS on rejected 1 MiB temporal roots while preserving admitted semantics. It did not measure creation speed.

Historical research-writer comparisons commonly preallocated `Segment * n` outside their timed arm because both compared mechanisms shared it. That was fair for those paired mechanism comparisons but is not a complete creation-cost bill for deciding whether lazy allocation should become the preferred native writer shape.

This gate charges segment-arena allocation in both candidates.

## Control / candidate

Control timing begins before allocating `(Segment * n)()` and therefore charges maximum segment output allocation **before** relation admission.

Candidate timing begins at the same boundary, executes relation admission first, and allocates `(Segment * n)()` only if admission enables segmentation.

Both arms then execute identical segmentation (when enabled), bounded Program construction, validation and direct canonical emission. Source/target bytes and their common ctypes input arrays are prebuilt outside the paired interval; this experiment isolates segment-allocation scheduling, not the entire ingest-copy boundary.

## Frozen matrix

Size: 1 MiB.

Cases from exact `_relation_cases(1 << 20)`:

- admitted: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- rejected: `fragmented_every32`, `independent_random`.

Use 21 paired alternating repetitions per case with cyclic GC disabled consistently. Force prior arm results out of scope before the next timer to avoid destructor/lifetime contamination.

## Falsifiable hypothesis

If eager maximum segment allocation is real creation work rather than harmless reservation, rejected roots should become materially faster when the gate prevents it. Admitted roots should remain near parity because both eventually allocate the same arena.

Disproof: any semantic mismatch invalidates the candidate; any admitted median lazy/eager wall or CPU >1.05 blocks promotion; either rejected case failing to reach <=0.95 wall and CPU blocks a creation-speed claim.

## Frozen decisions

`ADVANCE_LAZY_SEGMENT_TIMING` requires:

- exact relation decision, plan, Program, canonical wire and reconstructed roots for every row;
- each admitted case wall and CPU lazy/eager <= **1.05**;
- each rejected case wall and CPU lazy/eager <= **0.95**;
- rejected candidate segment-capacity bytes = 0;
- admitted candidate capacity = eager capacity.

Otherwise `HOLD_LAZY_SEGMENT_TIMING`; semantic disagreement -> `INVALIDATE_LAZY_SEGMENT_TIMING`.

## Hostile review

- Do not charge allocation only to eager; both arms start before any segment arena exists.
- Do not include source/target ctypes setup in only one arm.
- Do not claim whole-product creation speed; input conversion and observer work are outside this narrow gate.
- Do not weaken the rejected 0.95 gate if libc makes allocation cheap. If skipping 12 MiB does not produce measurable creation value, memory alone remains the reason to use lazy allocation.
- Do not infer that admitted maximum capacity is efficient merely because timing is parity.
- No representation, reader, v0.29 or deferred-v0.30 authority is earned.
