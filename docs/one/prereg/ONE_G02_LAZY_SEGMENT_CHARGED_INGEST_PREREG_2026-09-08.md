# ONE-G0.2 Lazy Segment — Charged Ingest Transfer Preregistration

**Date:** 2026-09-08  
**Experimental version:** `ONE-G0.2`

## Hypothesis

The promoted lazy Segment-arena scheduling rule remains measurably beneficial on rejected 1 MiB roots after charging source/target ctypes conversion and both root SHA-256 computations inside the writer interval, while admitted roots do not materially regress.

## Why this experiment exists

`ONE_G02_LAZY_SEGMENT_TIMING_RESULT_2026-09-08.md` proved the allocator scheduling effect inside the relation-to-wire envelope. That experiment deliberately shared source conversion and root-digest preparation outside timing. This transfer test widens the bill rather than re-running the same claim.

## Arms

Both arms perform, inside each timed call:

`bytes -> ctypes source/target arrays -> SHA-256(previous/current) -> relation admission -> conditional/eager Segment arena -> segmentation if admitted -> bounded Law + Surprise Program -> validation -> direct final-buffer canonical emission`

The only arm difference is Segment-arena scheduling:

- **eager:** reserve `(Segment * n)()` before relation admission;
- **lazy:** reserve it only after admission returns enabled.

Native compilation is common setup outside timing.

## Frozen matrix

Sizes:

- 64 KiB transfer/noise scale;
- 1 MiB decision scale.

Cases:

- admitted: `shift_plus1`, `shift_plus1_damage_quarter`, `fragmented_every96`;
- rejected: `fragmented_every32`, `independent_random`.

Repetitions: 15 paired alternating A/B-B/A per row.

## Semantic gates

For every row:

- eager and lazy admission/classification identical;
- exact full native segment plan identical when admitted;
- canonical wire/stats identical;
- exact two-root reconstruction;
- previous/current SHA-256 exact;
- admitted lazy arena capacity equals eager;
- rejected lazy arena capacity is zero.

Any semantic failure invalidates the experiment.

## Performance gate

Only the 1 MiB rows can advance the mechanism:

- every admitted row: lazy/eager median wall <= 1.05 and median CPU <= 1.05;
- every rejected row: lazy/eager median wall <= 0.97 and median CPU <= 0.97;
- no 64 KiB row may exceed 1.08 on either wall or CPU.

The 0.97 reject target is intentionally weaker than the preceding local 0.95 gate because conversion + two complete SHA-256 computations are now charged identically and dilute the allocator effect.

## Decision

- semantic failure -> `INVALIDATE_LAZY_SEGMENT_CHARGED_INGEST`;
- all performance/resource gates pass -> `ADVANCE_LAZY_SEGMENT_CHARGED_INGEST`;
- otherwise -> `HOLD_LAZY_SEGMENT_CHARGED_INGEST`.

Thresholds are frozen before result consumption.

## Claim boundary

A pass promotes lazy allocation across this broader Python/native research-writer envelope. It still does not establish archive traversal, filesystem metadata, authenticated placement/index construction, product-native throughput, reader-speed gains, or v0.29/v0.30 superiority.
