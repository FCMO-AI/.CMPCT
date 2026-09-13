# v0.30 EG08 read-cost hostile-review Mission Lock — 2026-09-13

Status: **preregistered hostile-review contract; research evidence only**

## Mission

EG08 preserves EG07 pack membership and bounded locality while selectively spending more Zstd creation effort on cold physical packs. Equal geometry proves that the number and raw size of physical decode units did not increase; it does **not** by itself prove that the resulting higher-effort frames preserve decode/extract/verification time or peak reader memory.

Before EG08 can receive product/frontier promotion credit, measure that exported reader cost on the same independently frozen eligible-nine transfer surfaces used by `docs/V030_EG08_ELIGIBLE9_TRANSFER_LOCK_2026-09-13.md`.

## Falsifiable hypothesis

For the same source tree and exact EG07/EG08 physical geometry, EG08's selected higher-effort frames do not create a confirmed extraction or strong-verification slowdown versus EG07 under the repository's existing same-runner timing confidence rule, and do not create a material reader-RSS regression.

A timing regression is confirmed only when the EG08 median is simultaneously:

- more than **5%** slower than EG07; and
- more than **3 ms** slower in absolute time.

Those values are inherited unchanged from `docs/PERFORMANCE_RELEASE_GATE.md`; they were not chosen after observing EG08.

The RSS result is reported per operation/workload and remains explicit debt if positive. This research referee does not invent a new release RSS threshold merely to promote or retire EG08.

## Frozen surfaces

Use exactly the nine preselected EG07-valid surfaces, with no additions/removals after seeing EG08:

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

## Same-semantics protocol

For each workload:

1. generate the source once and record its deterministic tree fingerprint;
2. fresh-process build EG07 and EG08 from that same source;
3. require both archives to strongly verify and require the already-frozen locality geometry to match;
4. time **fresh-process full extraction** for each archive with three repetitions and compare medians;
5. time **fresh-process strong verification** for each archive with three repetitions and compare medians;
6. record peak RSS for every operation;
7. require every extracted EG07 and EG08 user tree to equal the original source tree;
8. record archive bytes, raw decode-unit geometry, amplification, extraction CPU/wall, verification CPU/wall and RSS.

The operation boundaries must be identical between EG07 and EG08. No cache warming, different integrity setting, weaker verification path or reduced filesystem semantics is allowed for either contender.

## Hostile-review verdict

`EG08_READ_COST_SURVIVES` requires:

- all nine source fingerprints present;
- 9/9 strong verification and exact extracted-tree identity for both contenders;
- identical locality geometry EG07↔EG08 on all nine;
- zero confirmed extraction CPU or wall regressions under the inherited 5% + 3 ms rule;
- zero confirmed strong-verification CPU or wall regressions under the same rule.

Otherwise the verdict is `EG08_READ_COST_DEBT`, preserving every losing row. A debt does not erase EG08's density evidence; it blocks product/frontier promotion until repaired or deliberately adjudicated under a broader Pareto contract.

## Explicit non-goals

This referee does not change the EG08 effort ladder, pack membership, selectors, locality bound, integrity/recovery semantics, frozen Genesis scores, numeric version or ONE status. It is an exported-cost measurement, not a new compression search.

## Execution note — post-EG11

The contract above remains byte-for-byte unchanged in meaning after EG11. EG11 proved that EG08's exact bytes can be created with less duplicate encoder work; it does not answer whether those bytes export reader cost. Re-execute this already-frozen hostile review before giving EG08/EG11 frontier promotion credit. No threshold, surface, repetition count or timing rule is changed by this note.
