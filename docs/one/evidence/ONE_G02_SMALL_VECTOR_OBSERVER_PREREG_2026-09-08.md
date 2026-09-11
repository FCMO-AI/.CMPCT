# ONE-G0.2 one-slot small-vector observer handoff preregistration — 2026-09-08

## Mission lock / referee

The exact-prefix packed observer handoff has two simultaneously valid findings:

1. on opportunity-heavy `structured`, avoiding eager Python opportunity materialization is a large whole-writer win (~0.35x eager at 1 MiB);
2. the exact dense-size diagnostic at `f96ef04521d129df086bb4fd17d4332e4e8fc485` found a stable small-output regression on `near_repeats`, which emits exactly one 24-byte run record: ~1.115x at 256 KiB, ~1.114x at 384 KiB, ~1.102x at 512 KiB and ~1.097x at 1 MiB.

This experiment attacks the mechanism rather than adding a source-size threshold.

## Candidate

Use a one-slot small-vector transient handoff after the **same native observer scan**:

- zero opportunities: retain no payload;
- exactly one total run/reuse opportunity: copy its three integer fields into one inline scalar slot; do not call `ctypes.string_at` and do not construct a `RunOpportunity` / `ReuseOpportunity` object in the timed writer;
- two or more opportunities: use the existing exact used-prefix packed-byte representation.

The one-record boundary is structural: one fixed inline slot versus the bulk representation. It is not chosen from a fitted timing crossover. No source-size condition is allowed.

The handoff remains writer-internal transient observation state. It is not ONE wire syntax, a reader opcode, a persisted cache, or a separate compression mechanism.

## Falsifiable hypothesis

If the `near_repeats` debt is a fixed cost of creating/copying a tiny packed-byte prefix when eager materialization itself is tiny, the one-slot path should remove the stable >5% regressions without damaging the opportunity-heavy bulk win.

Disproof: if one-slot inline storage cannot close the small-output debt under fresh row-isolated timing, preserve the regression and stop elaborating this storage shape. The next direction becomes directly consuming native opportunities downstream rather than adding more handoff variants.

## Frozen experiment shape

Each `(size, family)` row runs in a separate fresh subprocess so allocator/cross-row state cannot create an apparent size cliff. Inside the child, 21 paired alternating repetitions compare eager `observe_native()` against the one-slot hybrid writer.

Sizes:

- 256 KiB
- 384 KiB
- 512 KiB
- 768 KiB
- 1 MiB

Families:

- `structured`
- `compressed_like`
- `long_runs`
- `random`
- `near_repeats`

Use the exact deterministic generators, root hashing, relation admission, segmentation, bounded Program construction, validation and direct canonical emission from the existing packed rehabilitation path.

## Hard semantic gates

For every row:

- hybrid materialization equals `observe_native(target)` exactly;
- observer counts, relation signature, segment plan, Program, canonical wire/stats and roots are exact across arms;
- decoded previous/current bytes are exact;
- inline representation is used iff total native opportunity count is exactly one; zero uses empty state; >1 uses bulk packed bytes.

Any semantic disagreement returns `INVALIDATE_SMALL_VECTOR_OBSERVER`.

## Frozen performance gates

A general small-vector advance requires all of the following:

1. every `near_repeats` row wall and CPU hybrid/eager <= **1.05**;
2. `structured` at 1 MiB wall and CPU hybrid/eager <= **0.60**;
3. no row in the complete 25-row matrix has wall or CPU hybrid/eager > **1.05**.

No averaging can hide a red row. The 0.60 structured gate preserves the mechanism-level breakthrough rather than accepting a small-output fix that destroys bulk economics.

Decisions:

- `ADVANCE_SMALL_VECTOR_OBSERVER` if semantics and all frozen performance gates pass;
- `HOLD_SMALL_VECTOR_OBSERVER` if semantics are exact but any performance gate fails;
- `INVALIDATE_SMALL_VECTOR_OBSERVER` on semantic disagreement.

## Hostile review / claim boundary

- The earlier packed positive and negative results remain immutable.
- Do not add a second inline slot or move the one-record boundary after seeing results.
- Do not add source-size gating after seeing results.
- Inline Python integers have heap cost; `retained_output_bytes` is only logical native record payload, not an RSS claim.
- Both arms still pay the same worst-case native scratch allocation during the scan.
- Downstream admission still does not consume observer opportunities; a pass advances only the transient handoff economics.
- This experiment earns no stored-byte, reader, access, recovery, portability, v0.29 or deferred-v0.30 authority.
