# ONE-G0.2 packed observer rehabilitation preregistration — 2026-09-08

## Mission lock / referee

Exact-head run `34214734980` at source `2dcc79ae7d62a21fde6006a65aed49ada49b54d5` returned `HOLD_COMPACT_OBSERVER_HANDOFF` with all semantic gates exact. The result is retained as a real negative for the tested arena-retaining compact view.

The failure pattern is mechanistically informative rather than a reason to weaken its frozen gates. At 1 MiB the arena-retaining compact arm was ~0.3156x eager on `structured` (12,288 observer opportunities, 294,912 useful native output bytes) but regressed on low-output rows: ~1.0832x `compressed_like` (0 useful output), ~1.0383x `long_runs` (5,280 useful bytes), ~1.0694x `random` (0 useful output), and ~1.0159x `near_repeats` (24 useful bytes). Every arm allocated the same ~3.54 MiB worst-case native output capacity. The compact arm uniquely retained those arenas through admission, Program construction, validation and canonical emission; the eager arm discarded them after Python materialization.

This rehabilitation experiment tests whether the exported cost is retained scratch capacity rather than compact handoff itself.

## Candidate

Keep the same native observer kernel and the same worst-case scratch allocation during the scan, but after the kernel returns:

1. copy only the used `_CRun` / `_CReuse` prefixes into exact-size transient bytes;
2. release the source-sized ctypes output arenas before downstream writer work;
3. keep counts/statistics and explicit out-of-band `materialize()` for semantic/oracle checks;
4. create zero Python `RunOpportunity` / `ReuseOpportunity` objects in the timed candidate writer.

The packed bytes are writer-internal transient state. They are not ONE wire syntax, a reader opcode, a persisted cache, or a new information model.

## Falsifiable hypothesis

If the prior control regressions were substantially caused by carrying ~3.54 MiB of mostly-empty native arenas through the rest of a 1 MiB writer call, then exact-size packing should preserve the large structured materialization win while restoring the low-opportunity rows to the inherited floor.

Disproof: if the packed candidate cannot retain the structured gain and close every 1 MiB >5% regression under the unchanged writer semantics, this rehabilitation shape is not worth further general writer work. Preserve the negative and redirect effort to a directly consumed native observation/admission boundary or kernel-side early falsification.

## Frozen matrix

Use the exact deterministic families and size matrix from `one_g02_compact_observer_handoff_writer.py`:

- sizes: 4 KiB, 256 KiB, 1 MiB;
- families: `structured`, `compressed_like`, `long_runs`, `random`, `near_repeats`;
- 15 paired alternating repetitions per arm;
- same independent previous-root generator;
- same root SHA-256, relation admission, native segmentation, bounded Program construction, validation and direct canonical emission.

The control is eager `observe_native()`. The candidate is `observe_native_packed()`.

## Hard semantic gates

For every row:

1. packed materialization equals `observe_native(target)` exactly;
2. observer counts, relation classification/proofs, segment plan, Program and canonical wire/stats are exact across arms;
3. decoded previous/current roots reconstruct byte-exactly;
4. root SHA-256 identities are exact;
5. packed retained output bytes equal used native output bytes and never exceed scratch capacity.

Any semantic disagreement returns `INVALIDATE_PACKED_OBSERVER_REHABILITATION` and prohibits performance interpretation.

## Frozen performance / gain-retention gates

Only 1 MiB rows vote.

The prior breakthrough row must remain materially present:

- `structured` median packed/eager wall <= **0.60**;
- `structured` median packed/eager CPU <= **0.60**.

Regression debt must close on the complete 1 MiB matrix:

- every family median packed/eager wall <= **1.05**;
- every family median packed/eager CPU <= **1.05**.

No aggregate average can compensate for a red row. The 0.60 gain-retention gate is intentionally much weaker than the observed ~0.316x seed so normal runner variance cannot erase a mechanism-level win, while still requiring a very large retained advantage.

## Resource accounting

Report, per row:

- worst-case native scratch capacity during the scan;
- useful native output bytes;
- candidate retained output bytes after packing;
- retained/scratch ratio;
- observer opportunity counts.

This modeled state is not an RSS claim. A passing candidate must face subprocess peak-RSS measurement before broader promotion.

## Decisions

- `ADVANCE_PACKED_OBSERVER_REHABILITATION`: all semantic gates pass, structured gain-retention passes, and every 1 MiB row closes the <=1.05 wall/CPU debt.
- `HOLD_PACKED_OBSERVER_REHABILITATION`: semantics exact but any frozen performance/resource gate fails.
- `INVALIDATE_PACKED_OBSERVER_REHABILITATION`: any semantic disagreement.

A pass advances only the writer-internal handoff shape. It earns no stored-byte, reader, access, recovery, portability, v0.29 or deferred-v0.30 authority.

## Hostile review frozen before result

- Do not relabel `compressed_like` as opportunity-rich after seeing its zero native opportunities; it remains in the matrix as a low-output hostile row and must not regress.
- Do not modify the previous `HOLD_COMPACT_OBSERVER_HANDOFF` thresholds or evidence.
- Pack/copy work and scratch-array destruction remain inside candidate timing.
- Authority materialization stays outside timing.
- Alternate arm order and disable cyclic GC consistently.
- Do not infer RSS from capacity accounting.
- Do not claim downstream native discovery consumption: current admission/segmentation still consume source/target bytes directly.
