# v0.30 EG12 persistent-CCtx mission lock — 2026-09-13

Status: **preregistered Forge experiment; no product or release credit**

Parent authority at lock: `b1416d73d366fc69d95487d53bac36a4768542cb`.

## Entering evidence

EG11 is the strongest known exact-EG08 creation path: it reproduced all nine frozen eligible surfaces byte-for-byte while reducing aggregate creation CPU/wall by about 1.32%. The subsequent EG08 ladder stopping oracle falsified every frozen shallow early-stop predicate. In particular, RAW/tie/early-size state does not prove that higher Zstd effort is futile, and skipping intermediate effort can lose exact selected bytes even when total stored size ties.

The remaining low-yield creation debt is therefore not eligible for another threshold-tuned stopping rule. The next allowed mechanism classes are (a) reuse compressor work/state while preserving the exact selected frames or (b) derive a genuinely stronger lower-bound/opportunity proof.

## Hypothesis

The research engines currently call the libzstd simple API `ZSTD_compress` repeatedly. That simple API is specified as a one-shot convenience path; repeated calls may pay context creation/setup work that is not part of the compression search itself.

A single persistent `ZSTD_CCtx`, reused across independent calls via `ZSTD_compressCCtx` while keeping the same input bytes and compression level per call, may reproduce the exact bytes emitted by the current `ZSTD_compress` path and reduce repeated setup work across EG11's effort ladder.

This is a state-reuse hypothesis, not an early-stop hypothesis. Every compression level still executes and every EG11 economic decision remains unchanged.

## Invariants

EG12 must preserve, without exception:

- exact complete-archive bytes versus EG11 on every frozen surface;
- exact per-call compressed frames versus the inherited simple API where directly checked;
- the same effort levels and ordering;
- the same admission law and raw-incumbent promotion behavior;
- the same physical membership and locality geometry;
- strong verification and tail recovery;
- filesystem semantics, integrity and recovery;
- no corpus-, filename- or extension-specific policy;
- no change to Genesis, R4, v0.29 or ONE evidence.

No format or reader change is authorized.

## Frozen referee surface

Use the same nine surfaces as the accepted EG11 referee:

Neutral/current15:

- `02_office_workspace`
- `04_analytics_and_database`
- `05_logs_and_telemetry`
- `09_ml_artifacts`
- `10_large_mixed_binary`

Hostile:

- `01_shifted_versions`
- `02_false_neighbors`
- `03_boundary_churn`
- `05_incompressible`

The current deterministic corpus producers are dependencies of the receipt.

## Disproof / retirement

The hypothesis is falsified for promotion if any of the following occurs:

1. any directly compared persistent-CCtx frame differs from the inherited `ZSTD_compress` frame;
2. any complete EG12 archive differs by one byte from EG11;
3. any strong-verify, tail-recovery or locality invariant differs;
4. a confirmed per-workload CPU or wall regression appears;
5. aggregate creation improvement is too small to justify carrying a new compressor-state path.

For item 5, the preregistered materiality bar is **at least 3% aggregate CPU reduction OR at least 0.5 s aggregate CPU reduction** versus EG11 on the nine-surface same-runner referee. Falling below both bars is a valid negative result even if byte identity holds.

The bar is a research carrying-cost test, not a product tuning constant.

## Acceptance

A result may be called `EG12_PERSISTENT_CCTX_PASSES` only when:

- 9/9 complete archives are byte-identical to EG11;
- direct frame-equivalence checks are all exact;
- all rows strong-verify and tail-recover;
- locality geometry is unchanged on all rows;
- no confirmed per-workload CPU/wall regression exists;
- peak RSS does not increase on any row;
- and the materiality bar above is met.

Otherwise preserve the receipt as negative evidence and do not create a follow-up that merely changes buffer sizes or timing boundaries.

## Hostile-review question

Even if persistent context is exact and faster, determine whether the gain is actual removal of libzstd setup work or merely benchmark-order/cache noise. The referee must therefore report call count, aggregate CPU/wall, per-workload ratios and RSS rather than accepting a single headline timing.

## Scope boundary

This experiment does not change compression density. It exists to test a mechanism explicitly allowed by the stopping-oracle result: reuse required work/state without deleting proof. If it fails or is immaterial, encoder micro-optimization is deprioritized and the Forge returns to exported read-cost/composition debt.