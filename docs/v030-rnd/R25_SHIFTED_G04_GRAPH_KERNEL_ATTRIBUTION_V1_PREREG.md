# r25 Shifted G0-G4 graph-kernel attribution v1 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION / FORGE D1 / R0 INSTRUMENTATION / ZERO PRODUCT OR RELEASE CREDIT**

Parent causal result: `R25_SHIFTED_G04_NESTED_STAGE_ATTRIBUTION_V2_RESULT.md`.

## Question

The mtime-stable nested-stage result proved that v0.28 graph construction owns ~95% of its child wall and attempt-5 Placement owns ~99.96%. Which already-existing primitive kernel owns enough of that graph wall to justify a lowest-sufficient optimization, and how much wall remains in nomination/control/packing outside those kernels?

## Frozen fixture and execution

- target: `resemblance_hostile_v1/01_shifted_versions`;
- root/descendant atime+mtime fixed to `1767225600000000000` ns before any measured child;
- exact historical tree SHA-256: `d9106dcdc8f965d45236c241d6c45f773e10b84ac204acc3c3521d889cd3a8fd`;
- three fresh-process repetitions, alternating `v028 -> attempt5`, `attempt5 -> v028`, `v028 -> attempt5`;
- builders, codecs, candidate order, thresholds and archive grammar unchanged.

## Frozen primitive timers

Monkeypatch timing wrappers may observe only these existing call boundaries; they may not change arguments, return values, call order or exceptions.

v0.28:
1. `delta_encode` aggregate wall and call count;
2. `_compress_record` aggregate wall and call count;
3. `similarity_sketch` aggregate wall and call count;
4. `lsh_candidates` aggregate wall and call count;
5. `_choose_pack_plan` aggregate wall and call count.

attempt-5 Placement:
1. `delta_encode` aggregate wall and call count;
2. `mosaic_delta_encode` aggregate wall and call count;
3. `_compress_record` aggregate wall and call count;
4. `_position_independent_candidates` aggregate wall and call count;
5. inherited `V028._choose_pack_plan` aggregate wall and call count.

Nested timers are reported individually and are not summed where one timed boundary contains another. The decision kernels are intentionally non-overlapping primitive encoders: v0.28 `delta_encode`; attempt-5 `delta_encode + mosaic_delta_encode`. Compression is reported separately.

## Frozen validity

`INVALID` if any repetition fails exact strong verification/tree identity; child archive identity is not deterministic within a kind; the mtime normalization is incomplete; the parent graph-stage call count is not exactly one; any primitive timer is negative/non-finite; or a wrapper changes the exact child bytes relative to the mtime-stable parent identities:

- v0.28: 1,761,588 B / `b483d7e1dda93b86c874eab4bf20649eedb709c42a5a8be428a8d7449786a851`;
- attempt-5: 1,723,056 B / `791baff9fe09b18588f26bdc47ff1b13f160ca095dff2e47b5523241e85c91e9`.

## Frozen measurements

For each kind retain medians of parent graph-stage wall, every primitive aggregate wall/calls, primitive/stage ratios, and the residual `max(0, stage - delta - mosaic - compress)` as a descriptive lower bound on non-encoder/non-compression work. Because timers can overlap with pack-plan/control wrappers, no sum involving pack-plan or nomination timers receives decision credit.

## Frozen decision grammar

Let `VD` = median v0.28 `delta_encode / graph_stage`; `AD` = median attempt-5 `(delta_encode + mosaic_delta_encode) / placement_stage`; `VC` and `AC` = compression/stage ratios.

- `SHIFTED_G04_DELTA_KERNEL_MATERIAL_BOTH`: `VD >= 0.20` and `AD >= 0.20`.
- `SHIFTED_G04_DELTA_KERNEL_MATERIAL_V028_ONLY`: `VD >= 0.20` and `AD < 0.20`.
- `SHIFTED_G04_DELTA_KERNEL_MATERIAL_ATTEMPT5_ONLY`: `AD >= 0.20` and `VD < 0.20`.
- `SHIFTED_G04_COMPRESSION_KERNEL_MATERIAL`: both delta-material tests are false and (`VC >= 0.20` or `AC >= 0.20`).
- `SHIFTED_G04_GRAPH_CONTROL_OR_NOMINATION_DOMINATES`: valid result matching none above.
- `INVALID`: any validity rule fails.

The 0.20 material band is frozen because a kernel below 20% of the already-dominant graph stage cannot by itself explain or recover the material post-PrefixGraph Shifted debt without an implausibly complete elimination. It is an intervention-selection threshold, not a release gate.

## Interpretation law

A delta-material result permits only exact-kernel work that preserves every candidate and returned byte; it does not authorize heuristic candidate dropping. A compression-material result redirects to redundant/avoidable compression work. A control/nomination result forces attribution earlier in candidate generation/control rather than another delta micro-optimization. Existing weak-prefix lower-bound, late-outer-bound, post-Placement stopping and edge-cache negatives remain binding.

No outcome grants product or release credit. Any Builder successor must independently prove complete-product wall improvement, exact bytes/tree, whole-process-tree RSS, recovery/integrity and release gates.
