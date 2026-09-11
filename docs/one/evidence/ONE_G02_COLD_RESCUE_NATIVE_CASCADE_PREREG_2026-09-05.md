# ONE-G0.2 — native cold-rescue cascade preregistration

Date: 2026-09-05
Experimental line: ONE-G0.2

## Mission Lock

The shared observer + unchanged sparse phase fallback recovered all 75 exact-relation positives in its frozen structural envelope. Four positives required fallback. The price remains unknown: 15 `fragmented_every32` negatives also reached the phase nominator.

The next experiment compares two opportunity-equivalent rescue strategies **only after shared observation is already silent**:

- **eager rescue:** run the existing exact safe relation dispatcher on every shared-silent pair;
- **gated rescue:** run the unchanged sparse phase certificate; only on nomination run the existing sparse relation falsifier; only when that gate fires does exact safe proof execute.

The already-paid shared observer is outside both timed rescue arms. Pair identity is also held constant. Nothing is gifted uniquely to the candidate.

## Why this is the correct baseline

Doing nothing after shared silence is cheaper but knowingly loses the four supported relations. Comparing against zero work would therefore compare different opportunity semantics. Eager exact rescue is the direct semantically equivalent way to close the shared-observer blind spot. The question is whether sparse discovery can preserve that opportunity coverage with substantially less compute.

## Frozen input

Use exactly the 34 shared-silent rows from the already-frozen complementarity matrix (sizes 4, 8, 16, 64, 256 KiB; seeds 13, 43, 67). This is intentional: the semantic set is already immutable, and the native implementation/timing gate did not exist when those results were produced.

By size, the rescue batches contain:

- 4 KiB: 9 pairs — 3 exact positives, 3 every32 negatives, 3 independent-random negatives;
- 8 KiB: 7 pairs — 1 exact positive, 3 every32 negatives, 3 random negatives;
- 16/64/256 KiB: 6 pairs each — 3 every32 and 3 random negatives.

## Native candidate implementation

The phase certificate remains semantically unchanged:

- stride 32;
- 8-byte little-endian words;
- source phases `{0,1,2,30,31}`;
- target phase 0;
- four bottom-hash witnesses per source phase;
- 240 bytes transient witness payload.

The native implementation may use a fixed four-entry max-heap per phase and sort the resulting 20 witnesses by hash before target audition. Those are direct algorithmic implementations of the frozen bottom-4 semantics, not parameter changes.

The existing native `one_g02_shift_relation_sparse_gate()` and exact safe dispatcher are reused unchanged.

Timing happens inside native code over complete same-size batches, with A-B-B-A ordering and repeated batches. Python selects the already-defined shared-silent rows before the timed call; that selection is common setup and is not part of either rescue strategy.

## Frozen promotion gate

Advance this cascade toward writer integration only if all are true:

- gated rescue exactly matches eager rescue's enabled/disabled decision and best shift on every shared-silent exact-positive pair;
- all four structurally known shared-miss positives remain recovered;
- no exact-negative pair becomes enabled;
- native phase witnesses exactly match the frozen Python phase-certificate reference on dedicated semantic vectors;
- median `gated / eager` rescue elapsed ratio across the five sizes is **<= 0.90x**;
- no size exceeds **1.05x** eager rescue;
- full exact-proof executions in the gated arm are **<= 60%** of eager rescue pair count over the complete 34-row matrix;
- every phase sample, sparse-gate compared byte, gate fire/reject, exact proof execution and transient-state byte is reported;
- pre-existing ONE semantic/hostile tests pass first.

The 0.90x requirement is a research-value threshold, not runner-noise tolerance: this extra cascade is only worthwhile if it buys clearly less rescue work. A marginal tie does not justify added writer complexity.

## Disproof

If the cascade misses a positive, the composition fails regardless of speed. If it preserves opportunity but does not clear the timing/proof-work gate, preserve the structural insight and retire this exact native cascade rather than weakening the gate or changing the frozen phase parameters.

A pass is still not a density or end-to-end writer victory. It only proves that, conditional on shared silence, sparse rescue is a better way to recover the same bounded-shift opportunities than eager exact proof.